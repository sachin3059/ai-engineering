import json
import os
from openai import OpenAI
from yahoo_finance_demo import get_stock_price

client = OpenAI(
    api_key=os.environ.get("SNOWFLAKE_TOKEN"),
    base_url=os.environ.get("SNOWFLAKE_BASE_URL"),
)

TOOL_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get the current price of a stock given its ticker symbol",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker_symbol": {
                        "type": "string",
                        "description": "The ticker symbol of the stock, e.g. AAPL",
                    }
                },
                "required": ["ticker_symbol"],
            },
        },
    }
]

SYSTEM_PROMPT = """
You are a stock agent that can fetch the current price of a stock given its ticker symbol.
Use the get_stock_price tool when you need live prices. Answer clearly in natural language.
"""

FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": "What is the current price of Apple's stock?",
    },
    {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "tool_call_id_1",
                "type": "function",
                "function": {
                    "name": "get_stock_price",
                    "arguments": json.dumps({"ticker_symbol": "AAPL"}),
                },
            }
        ],
    },
    {
        "role": "tool",
        "tool_call_id": "tool_call_id_1",
        "content": json.dumps(
            {"ticker": "AAPL", "price": 150.00, "currency": "USD"}
        ),
    },
    {
        "role": "assistant",
        "content": "Apple's stock price is $150.00 USD.",
    },
    {
        "role": "user",
        "content": "What are the current prices of Apple's and Tesla's stocks?",
    },
    {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "tool_call_id_2",
                "type": "function",
                "function": {
                    "name": "get_stock_price",
                    "arguments": json.dumps({"ticker_symbol": "AAPL"}),
                },
            },
            {
                "id": "tool_call_id_3",
                "type": "function",
                "function": {
                    "name": "get_stock_price",
                    "arguments": json.dumps({"ticker_symbol": "TSLA"}),
                },
            },
        ],
    },
    {
        "role": "tool",
        "tool_call_id": "tool_call_id_2",
        "content": json.dumps(
            {"ticker": "AAPL", "price": 150.00, "currency": "USD"}
        ),
    },
    {
        "role": "tool",
        "tool_call_id": "tool_call_id_3",
        "content": json.dumps(
            {"ticker": "TSLA", "price": 100.00, "currency": "USD"}
        ),
    },
    {
        "role": "assistant",
        "content": (
            "Apple's stock price is $150.00 USD. Tesla's stock price is $100.00 USD."
        ),
    },
]

AVAILABLE_TOOLS = {
    "get_stock_price": get_stock_price,
}


def _message_to_dict(message) -> dict:
    if isinstance(message, dict):
        return message
    return message.model_dump(exclude_none=True)


def run_agent(user_query: str) -> None:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *FEW_SHOT_EXAMPLES,
        {"role": "user", "content": user_query},
    ]

    print("\n" + "=" * 50)
    print(f"User: {user_query}\n")

    while True:
        response = client.chat.completions.create(
            model="openai-gpt-5-mini",
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
                tool_fn = AVAILABLE_TOOLS.get(fn_name)
                if tool_fn is None:
                    result = json.dumps({"error": f"Unknown tool: {fn_name}"})
                else:
                    result = tool_fn(**fn_args)
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


def main():
    print("Stock price agent (type quit to exit)")
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