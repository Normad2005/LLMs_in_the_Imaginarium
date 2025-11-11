import http.client
import json
from urllib.parse import urlencode
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_crypto_price(
    symbol: str,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Crypto Price API 取得即時加密貨幣價格。

    API 來源：
        crypto-price-by-api-ninjas.p.rapidapi.com

    說明：
        提供即時市場價格，支援數百種加密貨幣。

    參數：
        symbol (str): 加密貨幣代號，例如：BTC、ETH、DOGE。
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用的 RAPIDAPI_KEY。

    回傳：
        dict: 包含價格資訊的 JSON 物件，若解析錯誤則回傳 error。
    """
    conn = http.client.HTTPSConnection("crypto-price-by-api-ninjas.p.rapidapi.com")

    # 組 URL query，EX: /v1/cryptoprice?symbol=BTC
    query = f"/v1/cryptoprice?{urlencode({'symbol': symbol})}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "crypto-price-by-api-ninjas.p.rapidapi.com"
    }

    conn.request("GET", query, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
