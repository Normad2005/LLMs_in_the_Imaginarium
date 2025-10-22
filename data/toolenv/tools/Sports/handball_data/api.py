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