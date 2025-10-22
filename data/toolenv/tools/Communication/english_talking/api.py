import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰


def english_talking_get_answer(
    speech: str = "Hi",
    answer: str = "Hi, how are you?",
    user: str = "5ec479048958430d6a6d5895",
    status: str = "approved",
    _id: str = "5ec47b3d8958430d6a6d5898",
    page: int = 1,
    limit: int = 10,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 English Talking API，取得對話回答。

    來源: english-talking2.p.rapidapi.com

    參數：
        speech (str): 使用者輸入的開場對話，預設 "Hi"。
        answer (str): 對開場對話的回應內容，預設 "Hi, how are you?"。
        user (str): 對話建立者 ID。
        status (str): 對話狀態，可為 "approved" 或 "analyzing"。預設 "approved"。
        _id (str): 對話唯一識別碼。
        page (int): 分頁參數，預設 1。
        limit (int): 單頁筆數限制，預設 10。
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: API 回傳的 JSON 物件。
              若解析失敗則回傳 {"error": "...", "raw": "..."}。
    """

    conn = http.client.HTTPSConnection("english-talking2.p.rapidapi.com")

    # 建立查詢字串
    query = (
        f"/v1/dialog"
        f"?speech={speech}"
        f"&answer={answer.replace(' ', '%20')}"
        f"&user={user}"
        f"&status={status}"
        f"&_id={_id}"
    )

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "english-talking2.p.rapidapi.com",
        "page": str(page),
        "limit": str(limit)
    }

    # 發送 GET 請求
    conn.request("GET", query, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 嘗試解析 JSON 回傳
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
