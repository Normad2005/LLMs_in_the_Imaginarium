import http.client
import json
from urllib.parse import quote
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰


def get_salary_estimation(
    job_title: str,
    location: str,
    location_type: str = "ANY",
    years_of_experience: str = "ALL",
    fields: str = None,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 JSearch API，取得指定職位與地點的薪資估算資訊。

    參數：
        job_title (str): 職位名稱，例如 "nodejs developer"
        location (str): 地點，例如 "new york"
        location_type (str): 限縮地點層級，可選 ANY, CITY, STATE, COUNTRY（預設 ANY）
        years_of_experience (str): 年資範圍，可選：
            ALL, LESS_THAN_ONE, ONE_TO_THREE, FOUR_TO_SIX,
            SEVEN_TO_NINE, TEN_TO_FOURTEEN, ABOVE_FIFTEEN（預設 ALL）
        fields (str): 逗號分隔欄位清單，若為 None 則回傳所有欄位。
        toolbench_rapidapi_key (str): API 金鑰，預設為共用 RAPIDAPI_KEY。

    回傳：
        dict: API 回傳的 JSON 字典結果；
              若 JSON 解析失敗則回傳錯誤資訊。
    """

    conn = http.client.HTTPSConnection("jsearch.p.rapidapi.com")

    # 基礎查詢參數
    job_title = quote(job_title)
    location = quote(location)
    query = (
        f"/estimated-salary"
        f"?job_title={job_title}"
        f"&location={location}"
        f"&location_type={location_type}"
        f"&years_of_experience={years_of_experience}"
    )

    # 若 fields 有提供，加入 query
    if fields:
        query += f"&fields={fields}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "jsearch.p.rapidapi.com"
    }

    # 送出 GET request
    conn.request("GET", query, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # 回傳 JSON
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {
            "error": "Invalid JSON response",
            "raw": data.decode("utf-8")
        }
