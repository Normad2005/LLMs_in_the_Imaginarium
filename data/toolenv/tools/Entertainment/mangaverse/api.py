import http.client
import json
from urllib.parse import quote
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰


def search_manga(
    text: str,
    nsfw: str = "true",
    type: str = "all",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Mangaverse API 搜尋漫畫資訊。

    參數：
        text (str): 搜尋的文字，可為標題、作者或關鍵字，例如 "Naruto"。
        nsfw (str, optional): 是否包含 NSFW 內容。預設 'true'（全部）。可為 'true' 或 'false'。
        manga_type (str, optional): 漫畫來源。可為 'all', 'japan', 'china', 'korea'。
        toolbench_rapidapi_key (str, optional): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: API 回傳的 JSON 結果；若解析錯誤則返回錯誤訊息與原始資料。
    """
    conn = http.client.HTTPSConnection("mangaverse-api.p.rapidapi.com")

    text = quote(text)
    # 組合查詢參數
    query = (
        f"/manga/search"
        f"?text={text}"
        f"&nsfw={nsfw}"
        f"&type={type}"
    )

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "mangaverse-api.p.rapidapi.com"
    }

    # 發送 GET 請求
    conn.request("GET", query, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # JSON 解析
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
