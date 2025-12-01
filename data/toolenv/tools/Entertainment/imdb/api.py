import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_media_news(
    category: str = "MOVIE",
    first: int = 20,
    after: str = "",
    country: str = "US",
    language: str = "en-US",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 IMDb API 取得電影或影視資訊。

    說明：
        從 RapidAPI 的 imdb8.p.rapidapi.com 取得新聞或媒體相關資料，
        包含標題、年份、評分、上映日期、導演、演員、劇情等基本資訊。

    參數：
        category (str): 媒體類型，可為 "TOP", "MOVIE", "TV", "CELEBRITY", "UNKNOWN"。
                        預設為 "MOVIE"。
        first (int): 每次回傳的項目數（分頁用途），預設 20。
        after (str): 分頁游標，若為空則載入第一頁。
        country (str): 國家代碼，需搭配 language 使用。
        language (str): 語言代碼，需搭配 country 使用。
        toolbench_rapidapi_key (str): RapidAPI 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: API 回傳的 JSON 結果，若解析失敗則回傳錯誤訊息與原始資料。
    """

    conn = http.client.HTTPSConnection("imdb8.p.rapidapi.com")

    # 組合查詢字串
    query = (
        f"/news/v2/get-by-category?"
        f"category={category}"
        f"&first={first}"
        f"&country={country}"
        f"&language={language}"
    )

    if after:
        query += f"&after={after}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "imdb8.p.rapidapi.com"
    }

    # 發送請求
    conn.request("GET", query, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 嘗試解析 JSON
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
