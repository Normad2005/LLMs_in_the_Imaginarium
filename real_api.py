#Open Weather Map api connected

import requests
import wikipedia
from datetime import datetime, timedelta

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
    """
    取得天氣預報，可靈活使用 date 或 days。
    - location: 城市名稱
    - date: YYYY-MM-DD, 只返回該日期的預報
    - days: 取得未來幾天的預報（1-5）
    """
    # 計算可用日期範圍 (今天 ~ +5天)
    today = datetime.now().date()
    max_date = today + timedelta(days=5)

    # date 格式檢查與範圍檢查
    if date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return f"❌ 日期格式錯誤，請使用 YYYY-MM-DD。"
        if not (today <= date_obj <= max_date):
            return f"❌ {date} 不在未來五天範圍內，無法提供預報。"

    # days 範圍檢查
    if days is not None:
        if not (1 <= days <= 5):
            return f"❌ days 參數必須在 1~5 之間。"

    params = {
        "q": location,
        "appid": API_KEY,
        "units": "metric",
        "cnt": 40  # 40筆資料涵蓋5天的3小時預報
    }
    response = requests.get(FORECAST_URL, params=params)
    if response.status_code != 200:
        data = response.json()
        return f"❌ API 呼叫失敗: {data.get('message', 'Unknown error')}"
    
    forecasts = response.json()["list"]

    # 如果同時有 date 和 days，優先使用 date
    if date:
        forecasts = [item for item in forecasts if item["dt_txt"].startswith(date)]
    elif days:
        # 3小時一筆，一天8筆
        forecasts = forecasts[:days * 8]

    if not forecasts:
        return f"❌ 沒有可用的預報資料。"

    # 回傳格式化結果
    result = "\n".join(
        f"{item['dt_txt']}: {item['weather'][0]['description']}, {item['main']['temp']:.1f}°C"
        for item in forecasts
    )
    return f"Weather forecast for {location}:\n{result}"

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
