import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def generate_temp_upload_urls(
    account_id: str,
    video_id: str,
    source_name: str,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Fake Brightcove API 產生暫時上傳 URL。

    API 說明：
        "Temp Upload URLs" 用於生成指定帳號與影片的暫時上傳連結。

    參數：
        account_id (str): Brightcove 帳號 ID。
        video_id (str): 影片 ID。
        source_name (str): 來源檔案名稱。
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含 API 回應結果的 JSON 物件。
              若解析失敗，則回傳 {"error": ..., "raw": ...}
    """

    conn = http.client.HTTPSConnection("fake-brightcove.p.rapidapi.com")

    # 組合 API 路徑
    path = f"/v1/accounts/{account_id}/videos/{video_id}/upload-urls/{source_name}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "fake-brightcove.p.rapidapi.com"
    }

    # 發送 GET 請求
    conn.request("GET", path, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 嘗試解析 JSON
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
