import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # 可改成你自己的共用金鑰來源

def get_bart_schedule(orig="24th", dest="rock", toolbench_rapidapi_key: str = RAPIDAPI_KEY):
    """
    查詢 BART (Bay Area Rapid Transit) 抵達時間表。

    參數：
        orig (str): 起點站 (例: "24th")
        dest (str): 終點站 (例: "rock")
        toolbench_rapidapi_key (str): API 金鑰
    """
    conn = http.client.HTTPSConnection("community-bart.p.rapidapi.com")
    query = f"/sched.aspx?cmd=arrive&orig={orig}&dest={dest}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "community-bart.p.rapidapi.com"
    }

    try:
        conn.request("GET", query, headers=headers)
        res = conn.getresponse()
        raw_data = res.read()
        conn.close()

        # 嘗試解析 JSON，如果不是 JSON 可能是 XML 或純文字
        try:
            return json.loads(raw_data.decode("utf-8"))
        except:
            return {"raw": raw_data.decode("utf-8")}
    except Exception as e:
        return {"error": str(e)}
