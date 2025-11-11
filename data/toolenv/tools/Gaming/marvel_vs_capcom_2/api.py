import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰


def get_all_mvc2_characters(toolbench_rapidapi_key: str = RAPIDAPI_KEY):
    """
    取得 Marvel Vs Capcom 2 (MVC2) 遊戲中所有角色的資料。

    使用 RapidAPI 的 marvel-vs-capcom-2.p.rapidapi.com 服務。

    參數：
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含所有角色資料的 JSON 物件。
              若解析失敗，則回傳錯誤訊息與原始回應。
    """
    conn = http.client.HTTPSConnection("marvel-vs-capcom-2.p.rapidapi.com")

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "marvel-vs-capcom-2.p.rapidapi.com"
    }

    # 發送 GET 請求至 /characters
    conn.request("GET", "/characters", headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 嘗試解析 JSON
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}