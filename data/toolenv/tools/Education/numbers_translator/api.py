import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def spell_number(
    number_text: str,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Fun Translations Numbers API，將數字轉換成英文文字拼寫。

    參數：
        number_text (str): 要轉換的數字（例如 "238799111"）。
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含轉換結果的 JSON 物件。
              若解析失敗或 API 回應錯誤，則包含錯誤訊息。
    """
    conn = http.client.HTTPSConnection("api.funtranslations.com")

    # 組成 API 請求路徑
    endpoint = f"/translate/numbers.json?text={number_text}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "api.funtranslations.com",
        "Content-Type": "application/json"
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
