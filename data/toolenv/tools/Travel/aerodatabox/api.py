import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_airport_delay_statistics(codeType: str = "iata", code: str = "TPE", toolbench_rapidapi_key: str = RAPIDAPI_KEY):
    """
    參數：
        codeType (str): 機場代碼的類型。接受的值有：'iata'（3 碼，例如：'AMS', 'TPE'）或 'icao'（4 碼，例如：'EHAM', 'RCTP'）。預設為 'iata'。
        code (str): 對應 codeType 的機場代碼。若為 'iata' 則提供 3 碼（如 'TPE'）；若為 'icao' 則提供 4 碼（如 'RCTP'）。預設為 'TPE'。
    描述：
        返回指定機場的即時起飛和降落延誤統計數據。統計涵蓋 2 小時的觀察窗口，
        包括總航班數、取消數量、延誤時間中位數，以及起飛和降落的延誤指數。
    """
    conn = http.client.HTTPSConnection("aerodatabox.p.rapidapi.com")

    # 將 codeType 與 code 轉換為小寫以符合 API 路徑規範（或維持原樣，此處根據原範例 /icao/KLAX/ 處理）
    # 建立動態 URL 路徑
    path = f"/airports/{codeType.lower()}/{code.upper()}/delays"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "aerodatabox.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    # 發送 GET 請求
    conn.request("GET", path, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 嘗試解析 JSON
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}