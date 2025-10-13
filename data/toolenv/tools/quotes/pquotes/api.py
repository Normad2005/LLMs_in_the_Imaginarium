import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_fun_quote(topic: str = "fun", toolbench_rapidapi_key: str = RAPIDAPI_KEY):
    """
    呼叫 pquotes API 取得指定主題的名言。
    預設 topic='fun'
    """
    conn = http.client.HTTPSConnection("pquotes.p.rapidapi.com")

    payload = json.dumps({"topic": topic})

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "pquotes.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    conn.request("POST", "/api/quote", payload, headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    try:
        return json.loads(data.decode("utf-8"))
    except:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}