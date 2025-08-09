# mock_api.py

def get_weather(location, date):
    if not is_valid_date(date):
        raise ValueError("❌ get_weather only accepts date in YYYY-MM-DD format.")
    if location.lower() not in ["taipei", "london", "tokyo"]:
        raise ValueError(f"❌ get_weather does not support '{location}'. Try Taipei, London, or Tokyo.")
    return f"The weather in {location} on {date} is expected to be sunny with clouds."

def get_rain_chance(location, date):
    if not is_valid_date(date):
        raise ValueError("❌ get_rain_chance requires a valid ISO 8601 date.")
    if " " in location:
        raise ValueError("❌ get_rain_chance does not accept multi-word cities (e.g., 'New York').")
    return f"The chance of rain in {location} on {date} is 40%."

def get_temperature(location, date):
    if not is_valid_date(date):
        raise ValueError("❌ get_temperature requires exact date, not phrases like 'tomorrow'.")
    if location[0].islower():
        raise ValueError("❌ get_temperature requires the location name to start with a capital letter.")
    return f"The temperature in {location} on {date} will range between 24°C and 30°C."

# 共用的驗證函式
def is_valid_date(date_str):
    from datetime import datetime
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except:
        return False