import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_air_quality_data(
    city: str = None,
    state: str = None,
    country: str = None,
    lat: float = None,
    lon: float = None,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Air Quality API 取得指定地點的最新空氣品質資訊。
    提供 AQI 以及主要污染物濃度（CO, NO2, O3, SO2, PM2.5, PM10）。

    資料來源：air-quality-by-api-ninjas.p.rapidapi.com

    參數：
        city (str): 城市名稱。
        state (str): 州名（限美國）。
        country (str): 國家名稱。
        lat (float): 緯度（需與 lon 同時提供）。
        lon (float): 經度（需與 lat 同時提供）。
        toolbench_rapidapi_key (str): RapidAPI 金鑰（預設共用）。

    回傳：
        dict: 包含空氣品質與污染物資料的 JSON 物件。
              若 API 或解析錯誤則回傳 {"error": ...}
    """

    conn = http.client.HTTPSConnection("air-quality-by-api-ninjas.p.rapidapi.com")

    # === 建立查詢字串 ===
    query_params = []
    if city:
        query_params.append(f"city={city}")
    if state:
        query_params.append(f"state={state}")
    if country:
        query_params.append(f"country={country}")
    if lat is not None and lon is not None:
        query_params.append(f"lat={lat}")
        query_params.append(f"lon={lon}")

    query_string = "&".join(query_params)
    path = f"/v1/airquality?{query_string}" if query_string else "/v1/airquality"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "air-quality-by-api-ninjas.p.rapidapi.com"
    }

    # === 發送 GET 請求 ===
    conn.request("GET", path, headers=headers)
    res = conn.getresponse()
    data = res.read()
    conn.close()

    # === 嘗試解析 JSON ===
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
