import http.client
import json
from urllib.parse import urlencode
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def search_arxiv_papers(
    search_term: str,
    date_from: str = None,
    date_to: str = None,
    start: int = 0,
    date_type: str = "Submission Date",
    field: str = "All fields",
    num_results: int = 5,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 arXiv Research Paper Search API 搜尋學術論文。

    參數：
        search_term (str): 搜尋關鍵字 (必要)。
        date_from (str): 篩選的起始日期 (YYYY-MM-DD)。
        date_to (str): 篩選的結束日期 (YYYY-MM-DD)。
        start (int): 分頁起始索引，預設為 0。
        date_type (str): 日期篩選類型，預設為 'Submission Date'。
        field (str): 搜尋範圍 ('Title', 'Authors', 'Comments', 'All fields')。
        num_results (int): 要回傳的最大筆數，預設為 5。
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: API 回傳的 JSON 結果，若解析失敗則回傳錯誤訊息。
    """
    conn = http.client.HTTPSConnection("arxiv-research-paper-search.p.rapidapi.com")

    # 組合查詢參數
    params = {
        "search_term": search_term,
        "start": start,
        "date_type": date_type,
        "field": field,
        "num_results": num_results,
    }

    # 只有在 date_from/date_to 存在時才加入查詢字串
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to

    # urlencode 自動處理空白與特殊符號
    query_string = "/arxiv_search?" + urlencode(params)

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "arxiv-research-paper-search.p.rapidapi.com"
    }

    # 發送 GET 請求
    conn.request("GET", query_string, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 嘗試解析 JSON
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
