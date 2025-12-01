import http.client
import json
from urllib.parse import quote
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰


def search_cocktails(
    name: str = None,
    ingredients: str = None,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    搜尋雞尾酒配方與資訊。

    使用 Cocktail by API-Ninjas API，可依雞尾酒名稱或指定材料進行搜尋。

    參數：
        name (str): 雞尾酒名稱（支援部分字串，如 'bloody' 也會找到 bloody mary）。
        ingredients (str): 以逗號分隔的配料清單（如 'vodka,lemon juice'），
                           必須同時含有所有列出材料的雞尾酒才會被返回。
        toolbench_rapidapi_key (str): RapidAPI 金鑰，預設使用共用金鑰。

    回傳：
        dict 或 list：API 回傳的 JSON 結果。如果 JSON 解析失敗則回傳錯誤資訊。
    """

    conn = http.client.HTTPSConnection("cocktail-by-api-ninjas.p.rapidapi.com")

    # --- 建立查詢字串 ---
    params = []
    if name:
        name = quote(name)
        params.append(f"name={name}")
    if ingredients:
        params.append(f"ingredients={ingredients}")

    # 若兩者都沒提供，API 會返回大量資料，所以可視需求決定是否阻擋
    query_str = "/v1/cocktail"
    if params:
        query_str += "?" + "&".join(params)

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "cocktail-by-api-ninjas.p.rapidapi.com"
    }

    # --- 送出 GET 請求 ---
    conn.request("GET", query_str, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # --- 嘗試解析 JSON ---
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
