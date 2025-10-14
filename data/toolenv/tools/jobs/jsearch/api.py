import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_job_list(
    query: str = "developer jobs in chicago",
    country: str = "us",
    date_posted: str = "all",
    page: int = 1,
    num_pages: int = 1,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 jsearch API 取得職缺列表。
    預設搜尋 "developer jobs in chicago"
    """

    conn = http.client.HTTPSConnection("jsearch.p.rapidapi.com")

    endpoint = (
        f"/search?"
        f"query={query.replace(' ', '%20')}"
        f"&page={page}"
        f"&num_pages={num_pages}"
        f"&country={country}"
        f"&date_posted={date_posted}"
    )

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "jsearch.p.rapidapi.com"
    }

    conn.request("GET", endpoint, headers=headers)
    res = conn.getresponse()
    data = res.read()
    conn.close()

    try:
        return json.loads(data.decode("utf-8"))
    except:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
