import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_financial_data(
    function: str = "GLOBAL_QUOTE",
    symbol: str = "TSLA",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Alpha Vantage API 取得指定金融資料。
    可客製化 function 與 symbol。

    API 文件：
        https://rapidapi.com/alphavantage/api/alpha-vantage/

    參數：
        function (str): 要呼叫的資料功能名稱（預設 "GLOBAL_QUOTE"）。
        symbol (str): 股票代號（預設 "TSLA"）。
        toolbench_rapidapi_key (str): RapidAPI 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含金融資料的 JSON 物件。
              若解析失敗，回傳錯誤訊息與原始資料。
    """
    conn = http.client.HTTPSConnection("alpha-vantage.p.rapidapi.com")

    # 建立查詢字串
    query = f"/query?function={function}&symbol={symbol}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "alpha-vantage.p.rapidapi.com"
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
