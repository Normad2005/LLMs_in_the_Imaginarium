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
            raise Exception("Invalid date format. Please use YYYY-MM-DD.")
        
        today = datetime.now().date()
        if d != today:
            raise Exception("This API only supports querying the weather for today.")

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

#def get_rain_volume(location, date=None):
#    _validate_today(date)
#    params = {
#        "q": location,
#        "appid": API_KEY,
#        "units": "metric"
#    }
#    response = requests.get(BASE_URL, params=params)
#    data = response.json()
#    if response.status_code != 200:
#        raise Exception(data.get("message", "API call failed"))

#    rain = data.get("rain", {}).get("1h", 0.0)  # mm
#    return f"The rain volume in {location} over the last hour is {rain} mm."

from datetime import datetime, timedelta
import requests

def get_forecast(location, date=None, days=None):
    """Get weather forecast (1–5 days) for a given location."""
    today = datetime.now().date()
    max_date = today + timedelta(days=5)

    if date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD."
        if not (today <= date_obj <= max_date):
            return f"The date {date} is outside the 5-day forecast range. Only forecasts within the next 5 days are supported."

    if days is not None:
        if not (1 <= days <= 5):
            return "The 'days' parameter must be between 1 and 5."

    params = {
        "q": location,
        "appid": API_KEY,
        "units": "metric",
        "cnt": 40  # 40 data points = 5 days * 8 per day (3-hour intervals)
    }

    try:
        response = requests.get(FORECAST_URL, params=params)
        data = response.json()
        if response.status_code != 200:
            return f"Error: failed to fetch forecast ({data.get('message', 'Unknown error')})"
    except Exception as e:
        return f"Error: {e}"

    forecasts = data.get("list", [])

    if date:
        forecasts = [item for item in forecasts if item["dt_txt"].startswith(date)]
    elif days:
        forecasts = forecasts[:days * 8]

    if not forecasts:
        return "No forecast data available for the specified range."

    result = "\n".join(
        f"{item['dt_txt']}: {item['weather'][0]['description']}, {item['main']['temp']:.1f}°C"
        for item in forecasts
    )

    return f"Here is the weather forecast for {location}:\n{result}"


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
            return f"Error: failed to fetch exchange rate ({resp.text})"

        data = resp.json()
        rates = data.get("rates", {})
        rate = rates.get(target_currency.upper())

        if rate is None:
            return f"Unable to retrieve exchange rate from {base_currency.upper()} to {target_currency.upper()}."

        date_str = data.get("date")
        if date_str:
            note = " (latest available business day)" if date_str != datetime.now().strftime("%Y-%m-%d") else ""
        else:
            note = ""

        return (
            f"Here is the latest exchange rate:\n"
            f"1 {base_currency.upper()} = {rate:.4f} {target_currency.upper()} "
            f"(Date: {date_str}{note})"
        )
    except Exception as e:
        return f"Error: {e}"

# ========== 世界時間 ==========
def get_time_by_timezone(timezone):
    url = f"https://timeapi.io/api/Time/current/zone?timeZone={timezone}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return f"Error: failed to retrieve time for timezone '{timezone}' (status {resp.status_code})."

        data = resp.json()
        dt_str = data.get("dateTime")
        if not dt_str:
            return f"Error: invalid API response: {data}"

        dt = datetime.fromisoformat(dt_str)
        return f"The current time in {timezone} is {dt.strftime('%Y-%m-%d %H:%M:%S')}."
    except Exception as e:
        return f"Error: {e}"

# ========== 新聞 ==========
def get_latest_news(query, language="en"):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": language,
        "sortBy": "publishedAt",
        "pageSize": 3,
        "apiKey": NEWS_API_KEY
    }

    try:
        resp = requests.get(url, params=params)
        data = resp.json()
        if resp.status_code != 200 or data.get("status") != "ok":
            return f"Error: failed to fetch news ({data.get('message', data)})"

        articles = data.get("articles", [])
        if not articles:
            return f"No recent news articles found related to '{query}'."

        result = "\n".join([f"- {a['title']} ({a['url']})" for a in articles])
        return f"Here are the most relevant recent news articles about '{query}':\n{result}"
    except Exception as e:
        return f"Error: {e}"
