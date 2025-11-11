import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_animal_facts(
    name: str,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Animals by API Ninjas API，取得指定動物的科學與有趣知識。

    使用 RapidAPI 的 animals-by-api-ninjas.p.rapidapi.com 服務。

    參數：
        name (str): 動物的名稱（支援部分匹配，如 'fox' 可匹配 'red fox'）。
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict 或 list: 包含動物資料與科學事實的 JSON 物件或陣列。
                      若解析失敗則回傳錯誤訊息。
    """
    conn = http.client.HTTPSConnection("animals-by-api-ninjas.p.rapidapi.com")

    # 建立查詢字串
    query = f"/v1/animals?name={name}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "animals-by-api-ninjas.p.rapidapi.com"
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
