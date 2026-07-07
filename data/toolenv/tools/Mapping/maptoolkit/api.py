import http.client
import json
import urllib.parse
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰


def calculate_route(
    points: str,
    routeType: str = "",
    weighting: str = "networks",
    language: str = "en",
    voice_instructions: str = "",
    finish_instruction: str = "",
    format: str = "json",
    filename: str = "",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 MapToolkit Routing API，根據多個路線點計算路徑資訊。

    使用來源：
        maptoolkit.p.rapidapi.com

    功能描述：
        提供詳細的路線規劃資訊，支援多種交通模式（如自行車、步行等），
        可輸出 JSON、GPX 或 KML 格式，並支援語音導航指示。

    參數：
        points (str): 必填。路線的多個 Waypoint，格式為 `{lat},{lng}[|{lat},{lng}...]`，
                      至少需要 2 個座標點。例如：「47.5,8.5|47.6,8.6」。
        routeType (str): 選填。路線類型（例如 "bike"）。
        weighting (str): 選填。路線優化策略，僅在 routeType 為 "bike" 時有效。預設 "networks"。
        language (str): 選填。導航指示的語言，需為有效的 ISO 639-1 語言代碼。預設 "en"。
        voice_instructions (str): 選填。是否啟用語音導航（供文字轉語音引擎使用）。
        finish_instruction (str): 選填。是否在路線末端加入到達指示。
        format (str): 選填。回傳格式，可選 "json"、"gpx"、"kml"。預設 "json"。
        filename (str): 選填。檔案名稱，僅在 format 為 "gpx" 或 "kml" 時有效。
        toolbench_rapidapi_key (str): API 金鑰，預設共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含路線規劃結果的 JSON 物件，若 API 回傳非 JSON 則提供原始資料與錯誤訊息。
    """

    conn = http.client.HTTPSConnection("maptoolkit.p.rapidapi.com")

    # --- 建立查詢字串（只加入非空值的選填參數）---
    params = {"points": points}

    if routeType:
        params["routeType"] = routeType
    if weighting and weighting != "networks":
        params["weighting"] = weighting
    if language and language != "en":
        params["language"] = language
    if voice_instructions:
        params["voice_instructions"] = voice_instructions
    if finish_instruction:
        params["finish_instruction"] = finish_instruction
    if format and format != "json":
        params["format"] = format
    if filename:
        params["filename"] = filename

    query_string = urllib.parse.urlencode(params)
    path = f"/route?{query_string}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "maptoolkit.p.rapidapi.com"
    }

    # --- 發送請求 ---
    conn.request("GET", path, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # --- 嘗試解析 JSON ---
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
