import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_inflation_data(
    type: str = "CPI",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Inflation by API Ninjas API，取得 38 個主要國家的當前通膨數據。

    描述：
        提供全球 38 個主要國家的經濟通膨資料。
        數據通常每月更新，但部分國家可能延遲或更新頻率較低。

    參數：
        type (str): 通膨指標類型，可為：
                    - "CPI" (Consumer Price Index) 預設
                    - "HICP" (Harmonized Index of Consumer Prices)
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含各國通膨資訊的 JSON 物件。
              若解析失敗則回傳錯誤訊息與原始資料。
    """
    conn = http.client.HTTPSConnection("inflation-by-api-ninjas.p.rapidapi.com")

    # 加入 type 參數到查詢字串
    query = f"/v1/inflation?type={type}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "inflation-by-api-ninjas.p.rapidapi.com"
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
