import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_head_to_head_statistics(
    first_team: str = "Man United",
    second_team: str = "Liverpool",
    type_of_statistics: str = "full time result",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Football Dolphin API，
    取得英超球隊間的對戰統計資料（Head to Head Statistics）。

    參數：
        first_team (str): 第一支球隊名稱（預設："Man United"）。
        second_team (str): 第二支球隊名稱（預設："Liverpool"）。
        type_of_statistics (str): 統計類型，可選：
            - "full time result"
            - "home vs away full time result"
            - "result first half and the match"
            - "exact number of goals in the match"
            - "goals over"
            - "goals under"
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含對戰統計資料的 JSON 物件，若解析失敗則回傳錯誤訊息。
    """
    conn = http.client.HTTPSConnection("football-dolphin.p.rapidapi.com")

    # 組合查詢字串（注意需進行 URL 編碼）
    query = (
        f"/headtoheadstatistics/"
        f"?type_of_statistics={type_of_statistics.replace(' ', '%20')}"
        f"&first_team={first_team.replace(' ', '%20')}"
        f"&second_team={second_team.replace(' ', '%20')}"
    )

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "football-dolphin.p.rapidapi.com"
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
