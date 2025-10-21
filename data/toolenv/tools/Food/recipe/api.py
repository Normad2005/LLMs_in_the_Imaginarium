import http.client
import json
import urllib.parse
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_recipe(
    query: str = "italian wedding soup",
    offset: str = "",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Recipe API (by API Ninjas) 搜尋指定關鍵字的食譜。

    參數：
        query (str): 查詢的食譜關鍵字，預設為 'italian wedding soup'。
        offset (str): 分頁偏移量（可省略）。
        toolbench_rapidapi_key (str): RapidAPI 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict | list: 成功時回傳 API 回應的 JSON 物件（通常是食譜清單），
                     若解析失敗則回傳錯誤訊息與原始回應。
    """
    conn = http.client.HTTPSConnection("recipe-by-api-ninjas.p.rapidapi.com")

    # 使用 URL 編碼，避免空白或特殊字元錯誤
    encoded_query = urllib.parse.quote(query)
    query_string = f"/v1/recipe?query={encoded_query}"
    if offset:
        query_string += f"&offset={urllib.parse.quote(offset)}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "recipe-by-api-ninjas.p.rapidapi.com"
    }

    conn.request("GET", query_string, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
