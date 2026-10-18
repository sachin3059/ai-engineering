from pathlib import Path
import os

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

GEOCODE_URL = os.getenv(
    "GEOCODE_URL", "https://geocoding-api.open-meteo.com/v1/search"
)
FORECAST_URL = os.getenv("FORECAST_URL", "https://api.open-meteo.com/v1/forecast")
WEATHER_REQUEST_TIMEOUT = float(os.getenv("WEATHER_REQUEST_TIMEOUT", "10"))

SNOWFLAKE_TOKEN = os.getenv("SNOWFLAKE_TOKEN")
SNOWFLAKE_BASE_URL = os.getenv("SNOWFLAKE_BASE_URL")

MODEL = os.getenv("SNOWFLAKE_MODEL", "openai-gpt-5-mini")
