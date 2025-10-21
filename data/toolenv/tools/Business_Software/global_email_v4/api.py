import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def verify_email(email: str = "support@melissa.com", toolbench_rapidapi_key: str = RAPIDAPI_KEY):
    """
    參數：
        email (str): 要驗證的電子郵件地址。
    """
    conn = http.client.HTTPSConnection("global-email-v4.p.rapidapi.com")

    # 建立查詢字串
    query = (
        f"/v4/WEB/GlobalEmail/doGlobalEmail"
        f"?email={email}"
        f"&opt=VerifyMailbox:Express|VerifyMailbox:ExpressPremium"
        f"&format=json"
    )

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "global-email-v4.p.rapidapi.com"
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
