import streamlit as st
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

# ENV
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

st.set_page_config(page_title="AI Weather Agent", page_icon="🌤️")

st.title("🌤️ AI Weather Agent (FREE MCP)")
st.write("Ask weather like: **What is weather in Surat?**")

# ---------- WEATHER TOOL ----------
def get_weather(city):
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    )
    r = requests.get(url)
    data = r.json()

    if data.get("cod") != 200:
        return "City not found"

    return f"{data['main']['temp']}°C, {data['weather'][0]['description']}"

# ---------- MCP TOOL SCHEMA ----------
TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather of a city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string"}
            },
            "required": ["city"]
        }
    }
}]

# ---------- CALL OPENROUTER ----------
def call_llm(messages, tools=None):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto"
    }

    res = requests.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers=headers,
        data=json.dumps(payload)
    )

    return res.json()

# ---------- UI ----------
question = st.text_input("Ask your question")

if st.button("Ask"):
    if question:
        with st.spinner("Thinking..."):
            response = call_llm(
                messages=[{"role": "user", "content": question}],
                tools=TOOLS
            )

            msg = response["choices"][0]["message"]

            if "tool_calls" in msg:
                tool = msg["tool_calls"][0]
                city = json.loads(tool["function"]["arguments"])["city"]
                weather = get_weather(city)

                final = call_llm(
                    messages=[
                        {"role": "user", "content": question},
                        msg,
                        {
                            "role": "tool",
                            "tool_call_id": tool["id"],
                            "content": weather
                        }
                    ]
                )

                st.success(final["choices"][0]["message"]["content"])
            else:
                st.success(msg["content"])
