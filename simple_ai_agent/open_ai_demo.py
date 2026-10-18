# we will try to fetch stock price and stock ticker of apple using openai api

from openai import OpenAI
import os


client = OpenAI(
    api_key=os.environ.get("SNOWFLAKE_TOKEN"),
    base_url=os.environ.get("SNOWFLAKE_BASE_URL")
)

response = client.chat.completions.create(
    model="openai-gpt-5-mini",
    messages=[{
        "role": "user",
        "content": "What is Apple's stock price and ticker?"
    }],
    tools=[]
)

print(response.choices[0].message.content)







