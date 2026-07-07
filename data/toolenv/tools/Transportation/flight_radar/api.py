import http.client
import json
import urllib.parse
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰


def get_flights_in_bounding_box(
    bl_lat: float,
    bl_lng: float,
    tr_lat: float,
    tr_lng: float,
    limit: str = "300",
    speed: str = "",
    altitude: str = "",
    airline: str = "",
    type: str = "",
    airport: str = "",
    reg: str = "",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Flight Radar 1 API，列出指定地理邊界框內的所有即時航班。

    使用來源：
        flight-radar1.p.rapidapi.com

    功能描述：
        根據提供的左下/右上邊界座標，回傳該矩形區域內
        目前正在飛行中的航班列表，並支援多種篩選條件。
    """

    conn = http.client.HTTPSConnection("flight-radar1.p.rapidapi.com")

    # RapidAPI 的這個端點實際上是吃 north, south, east, west
    params = {
        "north": str(tr_lat),
        "south": str(bl_lat),
        "east": str(tr_lng),
        "west": str(bl_lng),
    }

    # 其他參數（如果有）就帶上去，讓 API 自行決定是否支援，或是留作紀錄
    if limit:
        params["limit"] = str(limit)
    if speed:
        params["speed"] = speed
    if altitude:
        params["altitude"] = altitude
    if airline:
        params["airline"] = airline
    if type:
        params["type"] = type
    if airport:
        params["airport"] = airport
    if reg:
        params["reg"] = reg

    query_string = urllib.parse.urlencode(params)
    path = f"/flights/v2/list-in-boundary?{query_string}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "flight-radar1.p.rapidapi.com"
    }

    conn.request("GET", path, headers=headers)
    res = conn.getresponse()
    data = res.read()
    conn.close()

    try:
        data_json = json.loads(data.decode("utf-8"))
        
        # 在 Python 端手動進行過濾，因為 API 不支援這些 query 參數
        flights = data_json.get("flightsList", [])
        if flights:
            filtered = []
            for f in flights:
                # 篩選航空公司 (callsign 通常包含 airline ICAO code)
                if airline and not str(f.get("callsign", "")).startswith(airline):
                    continue
                # 篩選機型 (icon)
                if type and str(f.get("icon", "")) != type:
                    continue
                # 篩選速度 min,max
                if speed and "," in speed:
                    s_min, s_max = map(float, speed.split(","))
                    f_speed = float(f.get("speed", 0))
                    if not (s_min <= f_speed <= s_max):
                        continue
                # 篩選高度 min,max
                if altitude and "," in altitude:
                    a_min, a_max = map(float, altitude.split(","))
                    f_alt = float(f.get("alt", 0))
                    if not (a_min <= f_alt <= a_max):
                        continue
                filtered.append(f)
            
            # 套用 limit
            if limit and limit.isdigit():
                filtered = filtered[:int(limit)]
                
            data_json["flightsList"] = filtered
            
        return data_json
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}