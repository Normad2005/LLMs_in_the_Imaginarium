import http.client
import json
from urllib.parse import quote
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_weather_forecast(
    q: str,
    days: int = 3,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 WeatherAPI 取得天氣預報資料。
    提供最多 14 天的每日與每小時天氣預報。

    參數：
        q (str): 查詢位置，可為：
            - 緯經度 (e.g. "48.8567,2.3508")
            - 城市名 (e.g. "Paris")
            - 郵遞區號 / Postal code
            - METAR / IATA / IP 位置（如 "auto:ip"）
        days (int): 預報天數 (最多 14)，預設為 3。
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含天氣預報資料的 JSON 物件。
              若解析失敗則回傳錯誤與原始字串。
    """
    conn = http.client.HTTPSConnection("weatherapi-com.p.rapidapi.com")

    # 組合查詢字串
    q = quote(q)
    query = f"/forecast.json?q={q}&days={days}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "weatherapi-com.p.rapidapi.com"
    }

    # 發送 GET 請求
    conn.request("GET", query, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 嘗試解析 JSON
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
