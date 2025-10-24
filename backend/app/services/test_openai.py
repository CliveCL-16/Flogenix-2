import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # loads .env file
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello Flowgenix!"}]
    )
    print("✅ OpenAI connection successful!")
    print("Response:", response.choices[0].message.content)
except Exception as e:
    print("❌ Connection failed:", e)
