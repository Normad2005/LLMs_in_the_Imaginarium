#Open Weather Map api connected

import requests

API_KEY = "01f863cd8a24c54dfe2042949f4d20e2"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# 地名 → 經緯度（可選）
city_coords = {
    "Taipei": (25.0330, 121.5654),
    "Tokyo": (35.6828, 139.7595),
    "London": (51.5074, -0.1278)
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

def get_rain_chance(location, date=None):
    params = {
        "q": location,
        "appid": API_KEY,
        "units": "metric"
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    if response.status_code != 200:
        raise Exception(data.get("message", "API call failed"))
    rain = data.get("rain", {}).get("1h", 0.0)
    return f"The chance of rain in {location} right now is estimated based on last hour rain volume: {rain} mm."
