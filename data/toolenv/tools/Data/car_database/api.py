import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_car_makes(toolbench_rapidapi_key: str = RAPIDAPI_KEY):
    """
    呼叫 Car Database API 取得所有汽車製造商 (makes) 列表。
    使用 RapidAPI 的 car-database.p.rapidapi.com 服務。

    參數：
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: JSON 物件，包含所有車廠資訊，若解析失敗則回傳錯誤訊息。
    """
    conn = http.client.HTTPSConnection("car-database.p.rapidapi.com")

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "car-database.p.rapidapi.com"
    }

    # 發送 GET 請求
    conn.request("GET", "/makes", headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 嘗試解析 JSON
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
