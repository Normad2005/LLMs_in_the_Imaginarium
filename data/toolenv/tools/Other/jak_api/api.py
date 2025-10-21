import http.client
import json
from config.api_keys import RAPIDAPI_KEY


def get_brawl_stars_data(toolbench_rapidapi_key: str = RAPIDAPI_KEY):
    """
    呼叫 JAK API 的 Brawl Stars 端點，取得遊戲相關資料。

    參數：
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 解析後的 JSON 回應，或錯誤資訊。
    """
    conn = http.client.HTTPSConnection("jak_api.p.rapidapi.com")

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "jak_api.p.rapidapi.com"
    }

    try:
        conn.request("GET", "/brawlStars", headers=headers)
        res = conn.getresponse()
        data = res.read()
        conn.close()

        try:
            return json.loads(data.decode("utf-8"))
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}

    except Exception as e:
        return {"error": str(e), "response": ""}


# ✅ 測試用
if __name__ == "__main__":
    result = get_brawl_stars_data()
    print(json.dumps(result, indent=2, ensure_ascii=False))
