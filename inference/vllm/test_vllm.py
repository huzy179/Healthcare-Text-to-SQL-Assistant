import os

from openai import OpenAI


client = OpenAI(
    base_url=os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1"),
    api_key=os.getenv("VLLM_API_KEY", "local"),
)

model = os.getenv("VLLM_MODEL", "healthcare-text-to-sql-model")

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": "Generate SQL for: Top 10 bệnh phổ biến nhất là gì?",
        }
    ],
    temperature=0,
)

print(response.choices[0].message.content)
