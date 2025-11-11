import http.client
import json
from config.api_keys import RAPIDAPI_KEY  # ← 共用金鑰

def calculate_mortgage_payment(
    interest_rate: float,
    loan_amount: float = 200000,
    home_value: float = 0,
    downpayment: float = 0,
    duration_years: int = 30,
    monthly_hoa: float = 0,
    annual_property_tax: float = 0,
    annual_home_insurance: float = 0,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    呼叫 Mortgage Calculator API，根據輸入參數計算房貸付款明細。

    使用來源：
        mortgage-calculator-by-api-ninjas.p.rapidapi.com

    功能描述：
        提供詳細的房貸與其他房屋融資支付資訊，
        使用標準的房貸公式計算利息、月繳與年繳金額。

    參數：
        interest_rate (float): 年利率（％）。例如 3.5 表示 3.5%。
        loan_amount (float): 貸款本金，預設 200000。
        home_value (float): 房屋總價，必須大於首付。
        downpayment (float): 首付款，不能超過房屋總價。
        duration_years (int): 貸款年限（1–10000），預設 30。
        monthly_hoa (float): 每月 HOA 費用（預設 0）。
        annual_property_tax (float): 年度房產稅。
        annual_home_insurance (float): 年度房屋保險費。
        toolbench_rapidapi_key (str): API 金鑰，預設共用 RAPIDAPI_KEY。

    回傳：
        dict: 包含計算結果的 JSON 物件，若 API 回傳非 JSON 則提供原始資料與錯誤訊息。
    """

    conn = http.client.HTTPSConnection("mortgage-calculator-by-api-ninjas.p.rapidapi.com")

    # --- 建立查詢字串 ---
    query = (
        f"/v1/mortgagecalculator?"
        f"loan_amount={loan_amount}"
        f"&interest_rate={interest_rate}"
        f"&home_value={home_value}"
        f"&downpayment={downpayment}"
        f"&duration_years={duration_years}"
        f"&monthly_hoa={monthly_hoa}"
        f"&annual_property_tax={annual_property_tax}"
        f"&annual_home_insurance={annual_home_insurance}"
    )

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "mortgage-calculator-by-api-ninjas.p.rapidapi.com"
    }

    # --- 發送請求 ---
    conn.request("GET", query, headers=headers)

    res = conn.getresponse()
    data = res.read()
    conn.close()

    # --- 嘗試解析 JSON ---
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
