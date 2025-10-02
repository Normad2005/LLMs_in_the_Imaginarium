import requests
import wikipedia
from datetime import datetime, timedelta

API_KEY = "01f863cd8a24c54dfe2042949f4d20e2"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
NEWS_API_KEY = "a8d26279a9a54f82abd34ea8f331ac70"

def _validate_today(date):
    if date:
        try:
            d = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise Exception("❌ 日期格式錯誤，請使用 YYYY-MM-DD。")
        today = datetime.now().date()
        if d != today:
            raise Exception(f"❌ 該API只能查詢今日的天氣。")

def get_current_weather(location, date=None):
    _validate_today(date)
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

def get_current_temperature(location, date=None):
    _validate_today(date)
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


def get_forecast(location, date=None, days=None):
    # 計算可用日期範圍 (今天 ~ +5天)
    today = datetime.now().date()
    max_date = today + timedelta(days=5)

    if date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return f"❌ 日期格式錯誤，請使用 YYYY-MM-DD。"
        if not (today <= date_obj <= max_date):
            return f"❌ {date} 不在未來五天範圍內，無法提供預報。"

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
    
# ========== 匯率 ==========
def get_exchange_rate(base_currency, target_currency):
    url = "https://api.frankfurter.app/latest"
    params = {"from": base_currency.upper(), "to": target_currency.upper()}
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return f"❌ 匯率查詢失敗: {resp.text}"
        data = resp.json()
        rates = data.get("rates", {})
        rate = rates.get(target_currency.upper())
        if rate is None:
            return f"❌ 無法取得 {base_currency.upper()} 對 {target_currency.upper()} 的匯率"
        return f"1 {base_currency.upper()} = {rate:.4f} {target_currency.upper()} (Date: {data.get('date')})"
    except Exception as e:
        return f"❌ 匯率查詢錯誤: {e}"

# ========== 世界時間 ==========
def get_time_by_timezone(timezone):
    url = f"https://worldtimeapi.org/api/timezone/{timezone}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return f"❌ 無法取得 {timezone} 的時間"
        data = resp.json()
        dt_str = data.get("datetime")
        if not dt_str:
            return f"❌ API 回傳無效資料: {data}"
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return f"The current time in {timezone} is {dt.strftime('%Y-%m-%d %H:%M:%S')}"
    except Exception as e:
        return f"❌ 取得時間失敗: {e}"


# ========== 新聞 ==========
def get_latest_news(query, language="en"):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": language,
        "sortBy": "publishedAt",
        "pageSize": 3,  # 回傳最新三則
        "apiKey": NEWS_API_KEY
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    if resp.status_code != 200 or data.get("status") != "ok":
        return f"❌ 新聞查詢失敗: {data.get('message', data)}"

    articles = data.get("articles", [])
    if not articles:
        return f"No recent news found for '{query}'."

    result = "\n".join([f"- {a['title']} ({a['url']})" for a in articles])
    return f"Latest news for '{query}':\n{result}"