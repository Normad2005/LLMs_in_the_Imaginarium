import http.client
import json
from urllib.parse import urlencode
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_airlines(
    name: str = "Singapore Airlines",
    icao: str = None,
    iata: str = None,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Airlines by API Ninjas 取得航空公司資訊。

    說明：
        可根據航空公司名稱、ICAO 或 IATA 代碼查詢。
        若未提供參數，預設查詢 "Singapore Airlines"。

    參數：
        name (str): 航空公司名稱（可部分比對），預設為 "Singapore Airlines"。
        icao (str): 國際民航組織 (ICAO) 三碼代碼。
        iata (str): 國際航空運輸協會 (IATA) 兩碼代碼。
        toolbench_rapidapi_key (str): RapidAPI 金鑰，預設使用共用 `RAPIDAPI_KEY`。

    回傳：
        dict | list: 包含航空公司資料的 JSON 結果。
    """
    conn = http.client.HTTPSConnection("airlines-by-api-ninjas.p.rapidapi.com")

    # 建立查詢參數
    params = {}
    if name:
        params["name"] = name
    if icao:
        params["icao"] = icao
    if iata:
        params["iata"] = iata

    query = f"/v1/airlines?{urlencode(params)}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "airlines-by-api-ninjas.p.rapidapi.com"
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
