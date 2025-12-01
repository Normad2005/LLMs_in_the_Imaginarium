import http.client
import json
from urllib.parse import quote
from config.api_keys import RAPIDAPI_KEY  # 共用金鑰


def get_lol_champion_stats(
    name: str,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    Retrieves the basic metadata and detailed in-game statistics for a specific
    League of Legends champion, including health, mana, attack damage,
    and various scaling stats.

    參數：
        name (str): 英雄名稱，例如 'Ekko', 'Jhin'。
        toolbench_rapidapi_key (str): RapidAPI 金鑰，預設為共用金鑰。

    回傳：
        dict: API 回傳的 JSON，若解析失敗則回傳錯誤訊息與原始資料。
    """
    conn = http.client.HTTPSConnection("league-of-legends-stats.p.rapidapi.com")

    # API 路徑，例如 /champions/ekko/stats
    name = quote(name.lower())
    path = f"/champions/{name}/stats"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "league-of-legends-stats.p.rapidapi.com"
    }

    # 發送 GET 請求
    conn.request("GET", path, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 解析回傳 JSON
    try:
        return json.loads(data.decode("utf-8"))
    except:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
