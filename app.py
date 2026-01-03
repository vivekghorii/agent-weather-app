from flask import Flask, request, jsonify, render_template
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ENV
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# ---------------- WEATHER TOOL ----------------
def get_weather(city):
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    )
    r = requests.get(url)
    data = r.json()

    if data.get("cod") != 200:
        return "City not found"

    temp = data["main"]["temp"]
    desc = data["weather"][0]["description"]
    return f"{temp}°C, {desc}"

# ---------------- MCP TOOL SCHEMA ----------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather of a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name like Surat, Delhi"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

# ---------------- CALL LLM (OPENROUTER) ----------------
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

    response = requests.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers=headers,
        data=json.dumps(payload)
    )

    return response.json()

# ---------------- MCP AGENT ----------------
@app.route("/ask", methods=["POST"])
def agent():
    question = request.json.get("question")

    response = call_llm(
        messages=[{"role": "user", "content": question}],
        tools=TOOLS
    )

    msg = response["choices"][0]["message"]

    # If model calls tool
    if "tool_calls" in msg:
        tool_call = msg["tool_calls"][0]
        args = json.loads(tool_call["function"]["arguments"])
        city = args["city"]

        tool_result = get_weather(city)

        final_response = call_llm(
            messages=[
                {"role": "user", "content": question},
                msg,
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": tool_result
                }
            ]
        )

        return jsonify({
            "reply": final_response["choices"][0]["message"]["content"]
        })

    # No tool needed
    return jsonify({
        "reply": msg["content"]
    })

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
