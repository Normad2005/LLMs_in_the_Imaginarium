import http.client
import json
from urllib.parse import quote
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰


def get_message(message_id: int = 2, 
                auth_token: str = "1234567890", 
                toolbench_rapidapi_key: str = RAPIDAPI_KEY):
    """
    呼叫 Colegio Santa Ana API，取得指定訊息內容。

    參數：
        message_id (int): 要查詢的訊息 ID（預設 2）
        auth_token (str): 授權用的 token（預設 "1234567890"）
    """

    conn = http.client.HTTPSConnection("colegiosantaana.p.rapidapi.com")

    # ✅ URL 編碼訊息 ID（保險起見）
    query = f"/api/mensajes/{quote(str(message_id))}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "colegiosantaana.p.rapidapi.com",
        "Authorization": auth_token,
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
    
def get_student_evaluations(
    student_id: int = 1,
    auth_token: str = "1234567890",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Colegio Santa Ana API，取得指定學生的評量資料。

    參數：
        student_id (int): 學生 ID（預設 1）
        auth_token (str): 授權 token（預設 "1234567890"）
    """

    conn = http.client.HTTPSConnection("colegiosantaana.p.rapidapi.com")

    # ✅ URL 編碼（保險用）
    query = f"/api/alumno/{quote(str(student_id))}/evaluaciones"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "colegiosantaana.p.rapidapi.com",
        "Authorization": auth_token,
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