import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_timezone_info(
    lat: float,
    lng: float,
    timestamp: int,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Stadia Time Zone Lookup API，取得指定位置與時間的時區資訊，
    包含夏令時間或其他偏移量資訊。

    參數：
        lat (float): 緯度，必填。
        lng (float): 經度，必填。
        timestamp (int): Unix 時間戳，必填。
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含時區資訊的 JSON 物件，若解析失敗則回傳錯誤訊息。
    """
    conn = http.client.HTTPSConnection("stadia-maps-time-zone-api.p.rapidapi.com")

    # 建立查詢字串
    query = f"/tz/lookup/v1?lat={lat}&lng={lng}&timestamp={timestamp}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "stadia-maps-time-zone-api.p.rapidapi.com"
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
