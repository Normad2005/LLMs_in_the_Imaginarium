import requests
import json
from config.api_keys import RAPIDAPI_KEY

def get_weather_data(data: str = "1", toolbench_rapidapi_key: str = RAPIDAPI_KEY):
    url = f"https://weather_dataset.p.rapidapi.com/data"
    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "weather_dataset.p.rapidapi.com"
    }
    params = {"data": data}

    try:
        response = requests.get(url, headers=headers, params=params, verify=False)  # 🚨 關閉 SSL 驗證
        return response.json()
    except Exception as e:
        return {"error": str(e)}
