import http.client
import json
import urllib.parse
from config.api_keys import RAPIDAPI_KEY


def search_businesses(
    query: str,
    limit: int = 20,
    lat: float = 37.359428,
    lng: float = -121.925337,
    zoom: str = "13",
    language: str = "en",
    region: str = "us",
    subtypes: str = "",
    verified: bool = False,
    business_status: str = "",
    extract_emails_and_contacts: bool = False,
    fields: str = "",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    🔍 Local Business Data%%Search Businesses
    使用關鍵字在 Google 地圖上搜尋商家和地點，支援地理偏向、分類篩選和聯絡資料豐富化。

    參數：
        query (str): 搜尋查詢或關鍵字（必要參數）。例如："Plumbers near New-York, USA"。
        limit (int): 傳回商家的最大數量，允許範圍為 1 到 500（預設為 20）。
        lat (float): 緯度座標，用於將搜尋結果偏向特定地點。
        lng (float): 經度座標，用於將搜尋結果偏向特定地點。
        zoom (str): 進行搜尋的縮放層級，與 lat 和 lng 共同決定視角範圍（預設為 "13"）。
        language (str): 使用標準 ISO 639-1 語言代碼設定結果語言（預設為 "en"）。
        region (str): 使用 ISO 3166 Alpha-2 代碼從特定區域或國家查詢 Google 地圖（預設為 "us"）。
        subtypes (str): 尋找特定子類型的商家，以逗號分隔。例如："Plumber,Carpenter,Electrician"。
        verified (bool): 是否僅傳回已驗證的商家（預設為 False）。
        business_status (str): 依商家營運狀態篩選。可選值："OPEN", "CLOSED_TEMPORARILY", "CLOSED"。
        extract_emails_and_contacts (bool): 是否透過抓取商家網站提取電子郵件、社群檔案和電話（預設為 False）。
        fields (str): 包含在回應中的特定欄位列表（逗號分隔）。例如："business_id,type,phone_number,full_address"。
        toolbench_rapidapi_key (str): API 金鑰，預設使用共用 RAPIDAPI_KEY。

    回傳：
        dict: 解析後的 JSON 回應，或錯誤資訊。
    """
    conn = http.client.HTTPSConnection("local-business-data.p.rapidapi.com")

    params = {
        "query": query,
        "limit": limit,
        "lat": lat,
        "lng": lng,
        "zoom": zoom,
        "language": language,
        "region": region,
        "subtypes": subtypes,
        "verified": str(verified).lower(),
        "business_status": business_status,
        "extract_emails_and_contacts": str(extract_emails_and_contacts).lower(),
        "fields": fields
    }

    query_string = f"/search?{urllib.parse.urlencode(params)}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "local-business-data.p.rapidapi.com",
        "User-Agent": "LocalBusinessScraper/1.0 (contact@example.com)"
    }

    try:
        conn.request("GET", query_string, headers=headers)
        res = conn.getresponse()
        data = res.read()
        conn.close()

        try:
            return json.loads(data.decode("utf-8"))
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}

    except Exception as e:
        return {"error": str(e), "response": ""}