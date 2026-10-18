import json
import sys
from pathlib import Path

import requests

# Allow `python tools/lookup_weather.py` from weather_agent/
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import FORECAST_URL, GEOCODE_URL, WEATHER_REQUEST_TIMEOUT

# WMO weather interpretation codes (Open-Meteo)
_WMO_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
}


def _wmo_label(code: int | None) -> str:
    if code is None:
        return "Unknown"
    return _WMO_DESCRIPTIONS.get(code, f"Weather code {code}")


def lookup_weather(location: str) -> str:
    """Return current weather for a city/place name as a JSON string."""
    location = (location or "").strip()
    if not location:
        return json.dumps({"error": "location must be a non-empty string"})

    try:
        geo = requests.get(
            GEOCODE_URL,
            params={"name": location, "count": 1, "language": "en", "format": "json"},
            timeout=WEATHER_REQUEST_TIMEOUT,
        )
        geo.raise_for_status()
        geo_data = geo.json()
        results = geo_data.get("results") or []
        if not results:
            return json.dumps(
                {"error": f"No location found for '{location}'", "location_query": location}
            )

        place = results[0]
        latitude = place["latitude"]
        longitude = place["longitude"]
        resolved_name = place.get("name", location)
        country = place.get("country")
        admin1 = place.get("admin1")

        forecast = requests.get(
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,relative_humidity_2m,apparent_temperature,"
                    "precipitation,weather_code,wind_speed_10m"
                ),
                "timezone": "auto",
            },
            timeout=WEATHER_REQUEST_TIMEOUT,
        )
        forecast.raise_for_status()
        forecast_data = forecast.json()
        current = forecast_data.get("current") or {}
        units = forecast_data.get("current_units") or {}

        weather_code = current.get("weather_code")
        payload = {
            "location_query": location,
            "resolved_name": resolved_name,
            "admin1": admin1,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "temperature": current.get("temperature_2m"),
            "temperature_unit": units.get("temperature_2m", "°C"),
            "apparent_temperature": current.get("apparent_temperature"),
            "relative_humidity": current.get("relative_humidity_2m"),
            "humidity_unit": units.get("relative_humidity_2m", "%"),
            "precipitation": current.get("precipitation"),
            "precipitation_unit": units.get("precipitation", "mm"),
            "wind_speed": current.get("wind_speed_10m"),
            "wind_speed_unit": units.get("wind_speed_10m", "km/h"),
            "weather_code": weather_code,
            "conditions": _wmo_label(weather_code),
            "observation_time": current.get("time"),
        }
        return json.dumps(payload)

    except requests.RequestException as exc:
        return json.dumps({"error": str(exc), "location_query": location})
    except (KeyError, TypeError, ValueError) as exc:
        return json.dumps({"error": f"Unexpected API response: {exc}", "location_query": location})


if __name__ == "__main__":
    print(lookup_weather("New York"))
