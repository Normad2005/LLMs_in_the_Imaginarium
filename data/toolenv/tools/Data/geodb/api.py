import http.client
import json
import urllib.parse
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_divisions_near_location(
    locationId: str = "33.832213-118.387099",
    radius: int = 100,
    distanceUnit: str = None,
    countryIds: str = None,
    excludedCountryIds: str = None,
    timeZoneIds: str = None,
    minPopulation: int = None,
    maxPopulation: int = None,
    namePrefix: str = None,
    namePrefixDefaultLangResults: bool = None,
    languageCode: str = None,
    asciiMode: bool = None,
    hateoasMode: bool = None,
    includeDeleted: str = None,
    limit: int = 1,
    offset: int = 0,
    sort: str = "SORT_FIELD",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    描述：
        傳回位於指定 GPS 座標特定半徑範圍內的行政區劃（城市、郡縣、島嶼或地區）列表。

    參數：
        locationId (str): 中心位置的 GPS 座標，格式為緯度後跟經度（例如：'33.832213-118.387099'）。
        radius (int): 尋找附近行政區劃的搜尋半徑。
        distanceUnit (str): 半徑的距離單位。可接受的值：'MI'（英里）或 'KM'（公里）。
        countryIds (str): 限制僅在這些國家/地區內的行政區劃。提供以逗號分隔的 ISO 國家代碼或 WikiData ID（例如：'US,CA'）。
        excludedCountryIds (str): 從結果中排除屬於這些國家/地區的行政區劃。
        timeZoneIds (str): 限制僅在這些時區內的行政區劃。
        minPopulation (int): 僅包含人口大於或等於此值的行政區劃。
        maxPopulation (int): 僅包含人口小於或等於此值的行政區劃。
        namePrefix (str): 僅傳回名稱以此字首開頭的行政區劃。
        namePrefixDefaultLangResults (bool): 當使用非預設語言進行名稱字首比對時，是否也與預設語言的名稱進行比對。
        languageCode (str): 顯示行政區劃名稱的語言（例如：'en', 'de', 'fr', 'ru'）。
        asciiMode (bool): 若為 true，則僅使用 ASCII 字元顯示結果，移除變音符號和特殊字元。
        hateoasMode (bool): 若為 true，則在回應中包含 HATEOAS 風格的分頁連結。
        includeDeleted (str): 是否包含被標記為刪除的行政區劃。可接受的值：'ALL', 'SINCE_YESTERDAY', 'SINCE_LAST_WEEK', 'NONE'。
        limit (int): 每次請求傳回的行政區劃結果的最大數量。
        offset (int): 結果集的從零開始的偏移量，用於分頁。
        sort (str): 指定結果的排序方式。格式為 '±SORT_FIELD'，其中 '+' 表示升序，'-' 表示降序（例如：'-population,+name'）。
    """
    conn = http.client.HTTPSConnection("wft-geo-db.p.rapidapi.com")

    # 建立動態查詢參數字典
    params = {
        "radius": radius,
        "limit": limit,
        "offset": offset
    }

    # 加入非必填參數（若有提供值）
    if distanceUnit is not None: params["distanceUnit"] = distanceUnit
    if countryIds is not None: params["countryIds"] = countryIds
    if excludedCountryIds is not None: params["excludedCountryIds"] = excludedCountryIds
    if timeZoneIds is not None: params["timeZoneIds"] = timeZoneIds
    if minPopulation is not None: params["minPopulation"] = minPopulation
    if maxPopulation is not None: params["maxPopulation"] = maxPopulation
    if namePrefix is not None: params["namePrefix"] = namePrefix
    if namePrefixDefaultLangResults is not None: params["namePrefixDefaultLangResults"] = str(namePrefixDefaultLangResults).lower()
    if languageCode is not None: params["languageCode"] = languageCode
    if asciiMode is not None: params["asciiMode"] = str(asciiMode).lower()
    if hateoasMode is not None: params["hateoasMode"] = str(hateoasMode).lower()
    if includeDeleted is not None: params["includeDeleted"] = includeDeleted
    if sort is not None: params["sort"] = sort

    # 將參數字典編碼為 URL 查詢字串
    query_string = urllib.parse.urlencode(params)
    query = f"/v1/geo/locations/{locationId}/nearbyDivisions?{query_string}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "wft-geo-db.p.rapidapi.com",
        "Content-Type": "application/json"
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