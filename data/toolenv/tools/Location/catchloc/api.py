import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def modify_group_info(
    timestamp: str,
    api_key: str,
    group_name: str,
    api: str,
    cert_key: str,
    group_key: str,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 CatchLoc API，修改地點群組資訊。

    API 說明：
        API access for modifying group information
        required parameter : api = "api.common.group.set.modify"

    參數：
        timestamp (str): 請求時間戳。
        api_key (str): 用戶的 API 金鑰。
        group_name (str): 群組名稱。
        api (str): API 指令（固定為 "api.common.group.set.modify"）。
        cert_key (str): 認證金鑰。
        group_key (str): 群組唯一識別鍵。
        toolbench_rapidapi_key (str): RapidAPI 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含修改結果的 JSON 物件，若解析失敗則回傳錯誤訊息。
    """
    conn = http.client.HTTPSConnection("catchloc.p.rapidapi.com")

    # 建立查詢字串
    query = (
        f"/api.partner.common.php"
        f"?timestamp={timestamp}"
        f"&api_key={api_key}"
        f"&group_name={group_name.replace(' ', '%20')}"
        f"&api={api}"
        f"&cert_key={cert_key}"
        f"&group_key={group_key}"
    )

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "catchloc.p.rapidapi.com"
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
