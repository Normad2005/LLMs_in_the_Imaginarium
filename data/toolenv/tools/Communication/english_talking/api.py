import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰


def get_dialog(
    speech: str = "Hello",                     # 使用者說的話
    answer: str = "Hi there! How are you?",    # 模擬回覆
    user: str = "5ec479048958430d6a6d5895",    # 預設使用者 ID
    status: str = "approved",                  # 預設狀態
    page: str = "1",                           # 預設頁碼
    limit: str = "5",                          # 預設筆數
    _id: str = None,                           # 可選 ID
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 English Talking API，模擬對話內容。
    
    參數：
        speech (str): 使用者輸入的文字。
        answer (str): 回覆內容。
        user (str): 使用者 ID。
        status (str): 篩選狀態（預設 approved）。
        page (str): 頁碼。
        limit (str): 單頁筆數。
        _id (str): 指定對話 ID（可選）。
    """

    conn = http.client.HTTPSConnection("english-talking2.p.rapidapi.com")

    # 組合查詢字串
    query = (
        f"/v1/dialog?"
        f"speech={speech}"
        f"&answer={answer}"
        f"&user={user}"
        f"&status={status}"
        f"&page={page}"
        f"&limit={limit}"
    )
    if _id:
        query += f"&_id={_id}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "english-talking2.p.rapidapi.com",
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