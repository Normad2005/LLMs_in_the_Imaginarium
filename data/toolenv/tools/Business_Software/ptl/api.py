import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # 如果你有共用金鑰

#沒意義的測試用api

def update_ptl_info(info1="111", info2="222", info3="333", toolbench_rapidapi_key: str = RAPIDAPI_KEY):
    """
    呼叫 PTL API 更新資訊。

    參數：
        info1 (str): 第一個參數
        info2 (str): 第二個參數
        info3 (str): 第三個參數
        toolbench_rapidapi_key (str): RapidAPI 金鑰
    """
    conn = http.client.HTTPSConnection("ptl.p.rapidapi.com")
    query = f"/update?info1={info1}&info2={info2}&info3={info3}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "ptl.p.rapidapi.com"
    }

    try:
        conn.request("GET", query, headers=headers)
        res = conn.getresponse()
        raw_data = res.read()
        conn.close()

        # 嘗試轉成 JSON
        try:
            return json.loads(raw_data.decode("utf-8"))
        except:
            return {"raw": raw_data.decode("utf-8")}
    except Exception as e:
        return {"error": str(e)}
