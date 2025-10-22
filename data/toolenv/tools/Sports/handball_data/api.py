import http.client
import json
from urllib.parse import quote
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰


def get_handball_scheduled_matches(
    date: str = "28/01/2021",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Handball Data API，取得指定日期的比賽列表。

    參數：
        date (str): 日期 (格式：DD/MM/YYYY)，預設為 28/01/2021
    """

    conn = http.client.HTTPSConnection("handball-data.p.rapidapi.com")

    # ✅ URL 編碼日期（防止斜線或空白錯誤）
    query_date = quote(date)
    query = f"/match/list/scheduled?date={query_date}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "handball-data.p.rapidapi.com",
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
    
def get_daily_handball_matches(
    date: str = "28/01/2021",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Handball Data API 取得每日比賽列表（包含即時比賽）。

    資料限制：
        - 僅支援查詢「今天 ±7 天」範圍內的日期。
        - 日期格式需為 dd/MM/yyyy。

    參數：
        date (str): 要查詢的比賽日期（預設: "28/01/2021"）。
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含比賽列表資料的 JSON 物件，
              若解析失敗則回傳錯誤訊息與原始資料。
    """
    conn = http.client.HTTPSConnection("handball-data.p.rapidapi.com")

    # 建立查詢字串，注意 date 需做 URL encode
    query = f"/match/list?date={date.replace('/', '%2F')}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "handball-data.p.rapidapi.com"
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