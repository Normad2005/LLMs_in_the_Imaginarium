import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_random_joke(toolbench_rapidapi_key: str = RAPIDAPI_KEY):
    """
    呼叫 Best Joke API 取得隨機笑話。
    使用 RapidAPI 的 bestjokeapi.p.rapidapi.com 服務。

    參數：
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含笑話內容的 JSON 物件，
              若解析失敗則回傳 {"error": "Invalid JSON response", "raw": ...}
    """
    conn = http.client.HTTPSConnection("bestjokeapi.p.rapidapi.com")

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "bestjokeapi.p.rapidapi.com"
    }

    # 發送 GET 請求
    conn.request("GET", "/jokes/random", headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 嘗試解析 JSON
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
