from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("OPENWEATHER_API_KEY")
print("API KEY:", API_KEY)


# -------- REAL TOOL (Weather API) --------
def get_weather(city):
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={API_KEY}&units=metric"
    )
    res = requests.get(url)
    data = res.json()

    if data.get("cod") != 200:
        return None

    temp = data["main"]["temp"]
    desc = data["weather"][0]["description"]
    return f"{temp}°C, {desc}"

# -------- AGENT --------
@app.route("/ask", methods=["POST"])
def agent():
    user_input = request.json.get("question", "").lower()

    if "weather" in user_input:
        city = user_input.split("in")[-1].replace("?", "").strip()
        weather = get_weather(city)

        if weather:
            return jsonify({
                "reply": f"The weather in {city.title()} is {weather}."
            })
        else:
            return jsonify({
                "reply": "City not found."
            })

    return jsonify({
        "reply": "Sorry, I cannot handle this request."
    })


@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

