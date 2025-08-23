#Open Weather Map api connected

import requests
import wikipedia

API_KEY = "api key"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

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

def get_forecast(location, date=None, days=None):
    params = {
        "q": location,
        "appid": API_KEY,
        "units": "metric",
        "cnt": 40  # 40筆資料涵蓋5天的3小時預報
    }
    response = requests.get(FORECAST_URL, params=params)
    data = response.json()
    if response.status_code != 200:
        raise Exception(data.get("message", "API call failed"))

    forecasts = data["list"]

    # 如果有指定 date，只保留該日期的預報
    if date:
        forecasts = [item for item in forecasts if item["dt_txt"].startswith(date)]

    # 如果有指定 days，則取未來幾天(天數8筆)
    elif days is not None:
        forecasts = forecasts[:days * 8]

    if not forecasts:
        return f"No forecast data available for {location}."

    return "Weather forecast for {}:\n{}".format(
        location,
        "\n".join(
            f"{item['dt_txt']}: {item['weather'][0]['description']}, {item['main']['temp']:.1f}°C"
            for item in forecasts
        )
    )

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
