import http.client
import json
from urllib.parse import urlencode
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def get_planet_data(
    name: str = None,
    min_mass: float = 0,
    max_mass: float = 0,
    min_radius: float = 0,
    max_radius: float = 0,
    min_period: float = 0,
    max_period: float = 0,
    min_temperature: float = 0,
    max_temperature: float = 0,
    min_distance_light_year: float = 0,
    max_distance_light_year: float = 0,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Planets by API Ninjas API，提供宇宙中行星與系外行星的天文資料。

    API 文件：
        https://rapidapi.com/api-ninjas/api/planets-by-api-ninjas/

    參數：
        name (str): 行星名稱（可選）。
        min_mass (float): 最小質量（單位：木星質量）。
        max_mass (float): 最大質量。
        min_radius (float): 最小半徑（木星半徑）。
        max_radius (float): 最大半徑。
        min_period (float): 最小公轉週期（地球日）。
        max_period (float): 最大公轉週期。
        min_temperature (float): 最小平均表面溫度（開爾文）。
        max_temperature (float): 最大平均表面溫度。
        min_distance_light_year (float): 最小距離（光年）。
        max_distance_light_year (float): 最大距離。
        toolbench_rapidapi_key (str): RapidAPI 金鑰（預設共用）。

    回傳：
        dict: 包含行星資料的 JSON 結構，或錯誤訊息。
    """
    conn = http.client.HTTPSConnection("planets-by-api-ninjas.p.rapidapi.com")

    # 構建查詢參數，只包含非 None 的值
    params = {
        "name": name,
        "min_mass": min_mass,
        "max_mass": max_mass,
        "min_radius": min_radius,
        "max_radius": max_radius,
        "min_period": min_period,
        "max_period": max_period,
        "min_temperature": min_temperature,
        "max_temperature": max_temperature,
        "min_distance_light_year": min_distance_light_year,
        "max_distance_light_year": max_distance_light_year
    }

    # 移除空值或預設為 0 的參數
    query = "?" + urlencode({k: v for k, v in params.items() if v not in [None, 0, ""]})

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "planets-by-api-ninjas.p.rapidapi.com"
    }

    # 發送 GET 請求
    conn.request("GET", f"/v1/planets{query}", headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
