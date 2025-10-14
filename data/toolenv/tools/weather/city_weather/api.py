# data/toolenv/tools/weather/weather_api138/api.py

import http.client
import json
from config.api_keys import RAPIDAPI_KEY 


def get_city_weather(city_name: str = "Taipei", toolbench_rapidapi_key: str = RAPIDAPI_KEY):
    """
    取得指定城市的即時天氣狀況。
    Args:
        city_name (str): 城市名稱（例如 'Taipei'）
    Returns:
        dict: 回傳 API JSON 結果，若錯誤則回傳 {"error": "..."}
    """
    try:
        conn = http.client.HTTPSConnection("weather-api138.p.rapidapi.com")

        headers = {
            "x-rapidapi-key": toolbench_rapidapi_key,
            "x-rapidapi-host": "weather-api138.p.rapidapi.com",
        }

        conn.request("GET", f"/weather?city_name={city_name}", headers=headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")

        try:
            json_data = json.loads(data)
        except json.JSONDecodeError:
            return {"error": f"Invalid JSON returned: {data}"}

        return json_data

    except Exception as e:
        return {"error": str(e)}
