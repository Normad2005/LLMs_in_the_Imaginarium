import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def convert_currency(
    base: str = "USD",
    target: str = "JPY",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Exchange Rate API 進行貨幣兌換。

    使用 RapidAPI 的 exchange-rate-api1.p.rapidapi.com 服務。

    參數：
        base (str): 三字母貨幣代碼，表示要轉換的原始貨幣（預設 "USD"）。
        target (str): 三字母貨幣代碼，表示要轉換的目標貨幣（預設 "JPY"）。
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含匯率資訊的 JSON 物件。
              若 API 回應無法解析為 JSON，則回傳錯誤訊息。
    """
    conn = http.client.HTTPSConnection("exchange-rate-api1.p.rapidapi.com")

    # 組合查詢字串
    query = f"/convert?base={base}&target={target}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "exchange-rate-api1.p.rapidapi.com"
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
