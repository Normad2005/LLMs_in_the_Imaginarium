import http.client
import json
import urllib.parse
from config.api_keys import RAPIDAPI_KEY


def get_trades_futures(
    market_venue: str = "BINANCE",
    base: str = "USDT",
    symbol: str = "BTC",
    sort: str = "asc",
    start: str = "2023-05-05T10:05:00",
    end: str = "2023-05-06T10:05:00",
    limit: int = 100,
    expiration: str = "perpetual",
    delivery_date: str = "",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    🎮 Cryptocurrency Financial Data%%Trades Futures
    根據交易所、交易對和時間範圍篩選公開的期貨交易記錄，並支援特定的合約到期類型。

    參數：
        market_venue (str): 交易所或場所名稱（例如：BINANCE）。
        base (str): 交易對中的基準貨幣（例如：USDT）。
        symbol (str): 交易對中的標的資產（例如：BTC）。
        sort (str): 結果的排序方式（asc: 由遠到近，desc: 由近到遠）。
        start (str): 請求時間段的開始時間。格式：YYYY-MM-DDTHH:MM:SS UTC。
        end (str): 請求時間段的結束時間。格式：YYYY-MM-DDTHH:MM:SS UTC。
        limit (int): 返回記錄的最大數量。最大值為 10000。
        expiration (str): 期貨合約的生命週期（perpetual, weekly, quarterly, monthly）。
        delivery_date (str): 期貨合約的最後有效日期。格式：YYYY-MM-DD。
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 解析後的 JSON 回應，或錯誤資訊。
    """
    conn = http.client.HTTPSConnection("cryptocurrency-financial-data.p.rapidapi.com")

    params = {
        "market_venue": market_venue,
        "base": base,
        "symbol": symbol,
        "sort": sort,
        "start": start,
        "end": end,
        "limit": limit,
        "expiration": expiration,
        "delivery_date": delivery_date
    }

    query = f"/trades/futures?{urllib.parse.urlencode(params)}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "cryptocurrency-financial-data.p.rapidapi.com",
        "User-Agent": "CryptoDataScraper/1.0 (contact@example.com)"
    }

    try:
        conn.request("GET", query, headers=headers)
        res = conn.getresponse()
        data = res.read()
        conn.close()

        try:
            return json.loads(data.decode("utf-8"))
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}

    except Exception as e:
        return {"error": str(e), "response": ""}