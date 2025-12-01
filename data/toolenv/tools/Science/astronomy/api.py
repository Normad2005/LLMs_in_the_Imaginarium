import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰


def get_celestial_body_position(
    body: str,
    from_date: str,
    to_date: str,
    latitude: float = 33.775867,
    longitude: float = -84.39733,
    elevation: float = 166,
    time: str = None,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Astronomy API，取得指定天體的觀測位置資訊（如方位角、仰角）。

    參數：
        body (str): 天體名稱，如 'Sun', 'Moon', 'Mars', 'Jupiter'。
        from_date (str): 起始日期，格式 'yyyy-mm-dd'。
        to_date (str): 結束日期，格式 'yyyy-mm-dd'。
        latitude (float): 觀測者緯度，預設 33.775867。
        longitude (float): 觀測者經度，預設 -84.39733。
        elevation (float): 海拔高度（公尺），預設 166。
        time (str): 時間 'HH:MM:SS'，可選。
        toolbench_rapidapi_key (str): API 金鑰，預設使用 RAPIDAPI_KEY。

    回傳：
        dict: JSON 解析結果，若解析失敗則包含 error 與 raw response。
    """
    conn = http.client.HTTPSConnection("astronomy.p.rapidapi.com")

    # 組合查詢字串
    query = (
        f"/api/v2/bodies/positions/{body}"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        f"&elevation={elevation}"
        f"&from_date={from_date}"
        f"&to_date={to_date}"
    )

    # 有 time 才加進 URL
    if time:
        query += f"&time={time}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "astronomy.p.rapidapi.com"
    }

    conn.request("GET", query, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    try:
        return json.loads(data.decode("utf-8"))
    except:
        return {
            "error": "Invalid JSON response",
            "raw": data.decode("utf-8")
        }
