import http.client
import json
import urllib.parse
from config.api_keys import RAPIDAPI_KEY


def list_of_deals(
    lower_price: int = 0,
    upper_price: int = 50,
    title: str = "batman",
    exact: int = 0,
    steam_app_id: str = "",
    store_id: str = "1,2,3",
    steam_rating: int = 0,
    metacritic: int = 0,
    on_sale: int = 0,
    aaa: int = 0,
    steamworks: int = 0,
    sort_by: str = "Deal Rating",
    desc: int = 0,
    output: str = "json",
    page_number: int = 0,
    page_size: int = 60,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    🎮 CheapShark%%List of Deals
    根據多種選填篩選條件（包括價格範圍、評分、商店和遊戲名稱）獲取分頁的遊戲特價列表。

    參數：
        lower_price (int): 最低價格（預設為 0）。
        upper_price (int): 最高價格（預設為 50，50 代表無限制）。
        title (str): 遊戲名稱關鍵字（預設為 "batman"）。
        exact (int): 是否精確匹配名稱（0=否，1=是）。
        steam_app_id (str): Steam App ID 列表（逗號分隔）。
        store_id (str): 商店 ID 列表（逗號分隔，預設為 "1,2,3"）。
        steam_rating (int): 最低 Steam 評價分數。
        metacritic (int): 最低 Metacritic 評分。
        on_sale (int): 是否僅限特價中（0=否，1=是）。
        aaa (int): 是否僅限 retail price > 29 的遊戲（0=否，1=是）。
        steamworks (int): 是否僅限 Steam 啟用（0=否，1=是）。
        sort_by (str): 排序基準（Deal Rating, Title, Savings, Price 等）。
        desc (int): 排序方向（0=升序，1=降序）。
        output (str): 輸出格式（預設為 "json"）。
        page_number (int): 頁碼（從 0 開始）。
        page_size (int): 每頁數量（最大 60）。
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 解析後的 JSON 回應，或錯誤資訊。
    """
    conn = http.client.HTTPSConnection("cheapshark-game-deals.p.rapidapi.com")

    params = {
        "lowerPrice": lower_price,
        "upperPrice": upper_price,
        "title": title,
        "exact": exact,
        "steamAppID": steam_app_id,
        "storeID": store_id,
        "steamRating": steam_rating,
        "metacritic": metacritic,
        "onSale": on_sale,
        "AAA": aaa,
        "steamworks": steamworks,
        "sortBy": sort_by,
        "desc": desc,
        "output": output,
        "pageNumber": page_number,
        "pageSize": page_size
    }

    query = f"/deals?{urllib.parse.urlencode(params)}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "cheapshark-game-deals.p.rapidapi.com",
        "User-Agent": "CheapSharkScraper/1.0 (contact@example.com)"
    }

    try:
        conn.request("GET", query, headers=headers)
        res = conn.getresponse()
        data = res.read()
        conn.close()

        try:
            return json.loads(data.decode("utf-8"))
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}

    except Exception as e:
        return {"error": str(e), "response": ""}