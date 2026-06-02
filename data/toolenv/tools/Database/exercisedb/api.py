import http.client
import json
import urllib.parse
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def search_exercises_by_name(
    name: str = "arm",
    limit: int = 10,
    offset: int = 0,
    sort_order: str = "ascending",
    sort_method: str = "id",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    根據運動名稱進行不區分大小寫的子字串搜尋。
    回傳詳細的運動資訊，包括目標肌群、輔助肌群、所需器材、步驟說明、難易度及分類。

    參數：
        name (str): 用於比對運動名稱的片段字串（例如：'arm'）。預設為 "arm"。
        limit (int): 每頁回傳的最大結果數量。基本方案上限為 10。預設為 10。
        offset (int): 分頁的起始索引（從 0 開始）。預設為 0。
        sort_order (str): 排序方向。可選值：'ascending'（升冪）或 'descending'（降冪）。預設為 "ascending"。
        sort_method (str): 排序依據的欄位。可選值：'bodyPart', 'id', 'name', 'target', 'equipment', 'difficulty', 'category'。預設為 "id"。
        toolbench_rapidapi_key (str): RapidAPI 的驗證金鑰。
    """
    conn = http.client.HTTPSConnection("exercisedb.p.rapidapi.com")

    # 建立與編碼查詢參數，避免參數內包含特殊字元或空格導致錯誤
    params = {
        "limit": limit,
        "sortOrder": sort_order,
        "sortMethod": sort_method,
        "offset": offset
    }
    query_string = urllib.parse.urlencode(params)
    
    # 組裝請求路徑（名稱需放入 URL 路徑中）
    query_path = f"/exercises/name/{urllib.parse.quote(name)}?{query_string}"

    headers = {
        'x-rapidapi-key': toolbench_rapidapi_key,
        'x-rapidapi-host': "exercisedb.p.rapidapi.com",
        'Content-Type': "application/json"
    }

    # 發送 GET 請求
    conn.request("GET", query_path, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 嘗試解析 JSON 
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}