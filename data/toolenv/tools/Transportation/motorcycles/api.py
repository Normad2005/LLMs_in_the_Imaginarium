import http.client
import json
from urllib.parse import urlencode
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰


def get_motorcycle_data(
    make: str = None,
    model: str = None,
    year: str = None,
    offset: int = 0,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Motorcycles by API Ninjas API，
    取得全球各廠牌摩托車的詳細技術資料。

    API 說明：
        Provides highly-detailed technical data on tens of thousands of
        different motorcycle models from hundreds of manufacturers.

    參數：
        make (str, optional): 廠牌名稱，可部分匹配 (例：'Harley' 會匹配 'Harley-Davidson')。
        model (str, optional): 車款名稱，可部分匹配 (例：'Ninja' 會匹配 'Ninja 650')。
        year (str, optional): 發售年份（格式：YYYY，例如 '2022'）。
        offset (int, optional): 結果偏移量，用於分頁，預設為 0。
        toolbench_rapidapi_key (str, optional): RapidAPI 金鑰（預設使用共用 RAPIDAPI_KEY）。

    回傳：
        dict: 包含查詢結果的 JSON 物件。
              若發生錯誤，則回傳錯誤訊息與原始內容。
    """

    conn = http.client.HTTPSConnection("motorcycles-by-api-ninjas.p.rapidapi.com")

    # 動態組合查詢參數
    params = {
        "make": make,
        "model": model,
        "year": year,
        "offset": offset
    }
    # 移除值為 None 的參數
    query = "/v1/motorcycles?" + urlencode({k: v for k, v in params.items() if v is not None})

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "motorcycles-by-api-ninjas.p.rapidapi.com"
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
