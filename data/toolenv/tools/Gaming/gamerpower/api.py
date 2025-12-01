import http.client
import json
from config.api_keys import RAPIDAPI_KEY


def get_filtered_game_giveaways(
    platform: str = "epic-games-store.steam.android",
    type_: str = "game.loot",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    🎮 GamerPower%%Filter & Group Giveaways
    篩選並分組目前的贈品活動。

    參數：
        platform (str): 遊戲平台（預設為 "epic-games-store.steam.android"）
        type_ (str): 類型（可為 "game", "loot" 等）
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 解析後的 JSON 回應，或錯誤資訊。
    """
    conn = http.client.HTTPSConnection("gamerpower.p.rapidapi.com")

    query = f"/api/filter?platform={platform}&type={type_}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "gamerpower.p.rapidapi.com"
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