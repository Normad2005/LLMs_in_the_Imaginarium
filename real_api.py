#Open Weather Map api connected

import requests
import wikipedia

API_KEY = "01f863cd8a24c54dfe2042949f4d20e2"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# 地名 → 經緯度（可選）
city_coords = {
    "Taipei": (25.0330, 121.5654),
    "Tokyo": (35.6828, 139.7595),
    "London": (51.5074, -0.1278),
    "Paris": (48.8566, 2.3522),
}

def get_weather(location, date=None):
    params = {
        "q": location,
        "appid": API_KEY,
        "units": "metric"
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    if response.status_code != 200:
        raise Exception(data.get("message", "API call failed"))
    desc = data["weather"][0]["description"]
    return f"The weather in {location} now is {desc}."

def get_temperature(location, date=None):
    params = {
        "q": location,
        "appid": API_KEY,
        "units": "metric"
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    if response.status_code != 200:
        raise Exception(data.get("message", "API call failed"))
    temp = data["main"]["temp"]
    return f"The temperature in {location} now is {temp:.1f}°C."

def get_rain_volume(location, date=None):
    params = {
        "q": location,
        "appid": API_KEY,
        "units": "metric"
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    if response.status_code != 200:
        raise Exception(data.get("message", "API call failed"))

    rain = data.get("rain", {}).get("1h", 0.0)  # mm
    return f"The rain volume in {location} over the last hour is {rain} mm."

def get_wikipedia_summary(query, sentences=2):
    try:
        summary = wikipedia.summary(query, sentences=sentences, auto_suggest=False, redirect=True)
        return f"Wikipedia summary for '{query}': {summary}"
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Multiple results found for '{query}': {', '.join(e.options[:5])}..."
    except wikipedia.exceptions.PageError:
        return f"No Wikipedia page found for '{query}'."
    except Exception as e:
        return f"Error: {e}"