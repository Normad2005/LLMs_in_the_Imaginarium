import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_ingest_status(
    account_id: str,
    video_id: str,
    job_id: str,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Fake Brightcove API 取得指定影片的 Ingest Job 狀態。

    API 說明：
        服務：fake-brightcove.p.rapidapi.com
        功能：查詢影片上傳 (Ingest) 任務狀態。

    參數：
        account_id (str): 帳戶 ID。
        video_id (str): 影片 ID。
        job_id (str): 上傳任務 (Ingest Job) ID。
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含 Ingest Job 狀態資訊的 JSON 物件。
              若解析失敗，則回傳 {"error": "...", "raw": "..."}。
    """
    conn = http.client.HTTPSConnection("fake-brightcove.p.rapidapi.com")

    # 建立查詢路徑（動態插入參數）
    endpoint = f"/v1/accounts/{account_id}/videos/{video_id}/ingest_jobs/{job_id}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "fake-brightcove.p.rapidapi.com"
    }

    # 發送 GET 請求
    conn.request("GET", endpoint, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 嘗試解析 JSON
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
