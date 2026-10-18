import json
import os
import sys
from pathlib import Path

from openai import OpenAI

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import MODEL, SNOWFLAKE_BASE_URL, SNOWFLAKE_TOKEN
from tools.lookup_weather import lookup_weather

VERBOSE = os.getenv("WEATHER_AGENT_VERBOSE", "").lower() in ("1", "true", "yes")

client = OpenAI(
    api_key=SNOWFLAKE_TOKEN or os.environ.get("SNOWFLAKE_TOKEN"),
    base_url=SNOWFLAKE_BASE_URL or os.environ.get("SNOWFLAKE_BASE_URL"),
)

TOOL_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "lookup_weather",
            "description": (
                "Get current weather for a city or place name using live forecast data"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City or place name, e.g. New York or London",
                    }
                },
                "required": ["location"],
            },
        },
    }
]

SYSTEM_PROMPT = """
You are a weather assistant. For any question about current weather in a place,
you must call lookup_weather with the place name. Do not invent temperatures or conditions.
Summarize the tool result in clear, friendly language.
"""

AVAILABLE_TOOLS = {
    "lookup_weather": lookup_weather,
}


def _message_to_dict(message) -> dict:
    if isinstance(message, dict):
        return message
    return message.model_dump(exclude_none=True)


def run_agent(user_query: str) -> None:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]

    print("\n" + "=" * 50)
    print(f"User: {user_query}\n")

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_DEFINITION,
        )

        choice = response.choices[0]
        assistant_message = choice.message
        messages.append(_message_to_dict(assistant_message))

        if assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                if VERBOSE:
                    print(f"[tool] {fn_name}({fn_args})")

                tool_fn = AVAILABLE_TOOLS.get(fn_name)
                if tool_fn is None:
                    result = json.dumps({"error": f"Unknown tool: {fn_name}"})
                else:
                    result = tool_fn(**fn_args)

                if VERBOSE:
                    print(f"[tool result] {result}\n")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )
            continue

        if assistant_message.content:
            print(f"Assistant: {assistant_message.content}\n")
        break


def main() -> None:
    if not (SNOWFLAKE_TOKEN or os.environ.get("SNOWFLAKE_TOKEN")):
        print("Set SNOWFLAKE_TOKEN (e.g. in weather_agent/.env)")
        sys.exit(1)
    if not (SNOWFLAKE_BASE_URL or os.environ.get("SNOWFLAKE_BASE_URL")):
        print("Set SNOWFLAKE_BASE_URL (e.g. in weather_agent/.env)")
        sys.exit(1)

    print("Weather agent (type quit to exit)")
    print("-" * 50)

    while True:
        query = input("\nYou: ").strip()
        if not query:
            continue
        if query.lower() == "quit":
            print("Goodbye!")
            break
        run_agent(query)


if __name__ == "__main__":
    main()
