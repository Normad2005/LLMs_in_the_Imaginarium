import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_industry_list(
    alias: str = "",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 SiteDomain API 取得產業兩位數代碼列表。

    使用 RapidAPI 的 sitedomain1.p.rapidapi.com 服務。

    參數：
        alias (str): 指定要查詢的別名（可為空字串）。
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含產業代碼清單的 JSON 物件，若解析失敗則回傳錯誤訊息。
    """
    conn = http.client.HTTPSConnection("sitedomain1.p.rapidapi.com")

    # 組合查詢路徑
    path = f"/codemeta/industry/list/{alias}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "sitedomain1.p.rapidapi.com"
    }

    # 發送 GET 請求
    conn.request("GET", path, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 嘗試解析 JSON
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}

def get_language_list(toolbench_rapidapi_key: str = RAPIDAPI_KEY):
    """
    呼叫 SiteDomain API，取得系統支援的語言列表。

    API 說明：
        Returns the list of available system languages.

    參數：
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含語言列表的 JSON 物件，若解析失敗則回傳錯誤訊息。
    """
    conn = http.client.HTTPSConnection("sitedomain1.p.rapidapi.com")

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "sitedomain1.p.rapidapi.com"
    }

    # 發送 GET 請求
    conn.request("GET", "/codemeta/language/list", headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 嘗試解析 JSON
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}