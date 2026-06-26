import http.client
import json
from urllib.parse import quote
from config.api_keys import RAPIDAPI_KEY


def search_amazon_products(
    query: str,
    page: int = 1,
    country: str = "US",
    sort_by: str = "RELEVANCE",
    product_condition: str = "ALL",
    min_price: int = None,
    max_price: int = None,
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    Search for Amazon products using keywords with optional filters.

    Parameters:
        query (str): Search keyword or phrase (e.g., "wireless headphones").
        page (int): Page number for pagination. Default is 1.
        country (str): Amazon marketplace country code (e.g., "US", "GB", "CA"). Default is "US".
        sort_by (str): Sort order. Options: "RELEVANCE", "LOWEST_PRICE", "HIGHEST_PRICE",
                       "REVIEWS", "NEWEST". Default is "RELEVANCE".
        product_condition (str): Filter by product condition. Options: "ALL", "NEW", "USED",
                                 "RENEWED". Default is "ALL".
        min_price (int): Minimum price filter (in the country's currency). Optional.
        max_price (int): Maximum price filter (in the country's currency). Optional.
        toolbench_rapidapi_key (str): RapidAPI key.

    Returns:
        dict: JSON response containing product search results.
    """
    conn = http.client.HTTPSConnection("real-time-amazon-data.p.rapidapi.com")

    query_params = f"query={quote(query)}&page={page}&country={country}&sort_by={sort_by}&product_condition={product_condition}"
    if min_price is not None:
        query_params += f"&min_price={min_price}"
    if max_price is not None:
        query_params += f"&max_price={max_price}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "real-time-amazon-data.p.rapidapi.com"
    }

    conn.request("GET", f"/search?{query_params}", headers=headers)
    res = conn.getresponse()
    data = res.read()
    conn.close()

    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
