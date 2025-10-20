import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_f1_latest_news(toolbench_rapidapi_key: str = RAPIDAPI_KEY):
    """
    呼叫 F1 Latest News API 取得最新的 F1 賽車新聞。
    使用 RapidAPI 的 f1-latest-news.p.rapidapi.com 服務。

    參數：
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含最新 F1 新聞的 JSON 物件，
              若解析失敗則回傳錯誤訊息與原始資料。
    """
    conn = http.client.HTTPSConnection("f1-latest-news.p.rapidapi.com")

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "f1-latest-news.p.rapidapi.com"
    }

    # 發送 GET 請求
    conn.request("GET", "/news", headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 嘗試解析 JSON
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
