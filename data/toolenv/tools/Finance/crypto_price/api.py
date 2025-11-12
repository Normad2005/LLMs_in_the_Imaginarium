import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_crypto_price(
    symbol: str,
    base: str = "USDT",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    取得即時加密貨幣行情資料。
    使用 RapidAPI 的 crypto-market-prices.p.rapidapi.com 服務。

    參數：
        symbol (str): 加密貨幣代號（例如 BTC、ETH、BNB），不分大小寫。
        base (str): 對應報價幣別，可為法幣或其他加密貨幣，預設 "USDT"。
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含加密貨幣價格資訊的 JSON 物件。
              若解析失敗或 API 錯誤，回傳錯誤訊息與原始內容。
    """
    conn = http.client.HTTPSConnection("crypto-market-prices.p.rapidapi.com")

    # 組合查詢路徑，例如 /tokens/BTC?base=USDT
    path = f"/tokens/{symbol.upper()}?base={base.upper()}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "crypto-market-prices.p.rapidapi.com"
    }

    # 發送 GET 請求
    conn.request("GET", path, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 嘗試解析 JSON 回應
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
