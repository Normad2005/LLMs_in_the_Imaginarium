import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_thailand_info(toolbench_rapidapi_key: str = RAPIDAPI_KEY):
    """
    呼叫 Thailand API (thailand.p.rapidapi.com)。
    若無特定 endpoint，預設執行根目錄 '/' 查詢。

    參數：
        toolbench_rapidapi_key (str): RapidAPI 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 回傳 JSON 結果，若解析失敗則回傳原始資料。
    """
    conn = http.client.HTTPSConnection("thailand.p.rapidapi.com")

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "thailand.p.rapidapi.com"
    }

    # 發送 GET 請求（根目錄）
    conn.request("GET", "/", headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 嘗試解析 JSON
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
