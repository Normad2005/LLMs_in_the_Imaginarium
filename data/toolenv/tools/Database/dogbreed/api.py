import http.client
import json
from urllib.parse import quote
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_dog_breeds_metadata(
    search: str,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Dog Breed DB API，取得指定搜尋字串相關的狗品種基本資訊。

    描述：
        Provides the basic metadata on all breeds of dogs from around the world.

    參數：
        search (str): 查詢字串，可部分比對。例如 '*alaskan'
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: API 回傳的 JSON 資料。
              若解析失敗，則回傳 {"error": "...", "raw": "..."}。
    """

    conn = http.client.HTTPSConnection("dogbreeddb.p.rapidapi.com")

    # 組合查詢路徑
    search = quote(search)
    query = f"/?search={search}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "dogbreeddb.p.rapidapi.com"
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
