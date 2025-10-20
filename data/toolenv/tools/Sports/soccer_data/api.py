import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_soccer_tournaments(toolbench_rapidapi_key: str = RAPIDAPI_KEY):
    """
    呼叫 Soccer Data API 取得足球賽事清單。
    使用 RapidAPI 的 soccer-data.p.rapidapi.com 服務。

    參數：
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含足球賽事清單的 JSON 物件，若解析失敗則回傳錯誤訊息。
    """
    conn = http.client.HTTPSConnection("soccer-data.p.rapidapi.com")

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "soccer-data.p.rapidapi.com"
    }

    # 發送 GET 請求至 /tournament/list
    conn.request("GET", "/tournament/list", headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 嘗試解析 JSON
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
