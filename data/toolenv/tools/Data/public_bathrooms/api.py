import http.client
import json
from urllib.parse import urlencode
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def search_public_restrooms(
    states: str = "NY,FL",
    lat: float = None,
    lon: float = None,
    page: int = 1,
    per_page: int = 10,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Public Bathrooms API 搜尋全球公共廁所。

    API 來源：
        public-bathrooms.p.rapidapi.com
        擁有超過 60,000 筆公共廁所資料，支援依地點或州別查詢。

    參數：
        states (str): 美國州縮寫的逗號分隔清單，例如 "NY,FL"。
        lat (float): 搜尋中心點的緯度（可選）。
        lon (float): 搜尋中心點的經度（若使用 lat 則必填）。
        page (int): 頁碼，預設為 1。
        per_page (int): 每頁筆數，預設為 10。
        toolbench_rapidapi_key (str): RapidAPI 金鑰，預設使用共用金鑰。

    回傳：
        dict: JSON 格式的查詢結果，若解析失敗則包含錯誤訊息。
    """
    conn = http.client.HTTPSConnection("public-bathrooms.p.rapidapi.com")

    # 建立查詢參數
    params = {
        "states": states,
        "page": page,
        "per_page": per_page
    }

    # 若提供經緯度則加入
    if lat is not None and lon is not None:
        params["lat"] = lat
        params["lon"] = lon

    query = f"/api/getByStates?{urlencode(params)}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "public-bathrooms.p.rapidapi.com"
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
