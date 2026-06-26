import http.client
import json
from config.api_keys import RAPIDAPI_KEY


def search_streaming_shows(
    country: str,
    catalogs: str = None,
    show_type: str = None,
    genres: str = None,
    keyword: str = None,
    order_by: str = "original_title",
    order_direction: str = "asc",
    series_granularity: str = "show",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    Search for TV shows and movies by filters across streaming services worldwide.

    Parameters:
        country (str): ISO 3166-1 alpha-2 country code (e.g., "us", "gb", "ca"). Required.
        catalogs (str): Comma-separated streaming service IDs to filter by
                        (e.g., "netflix", "prime", "disney"). If omitted, searches all services.
        show_type (str): Filter by content type. Options: "movie", "series". If omitted, returns both.
        genres (str): Comma-separated genre IDs to filter by (e.g., "action", "comedy").
        keyword (str): Keyword to search for in the show title or description.
        order_by (str): Field to order results by. Options: "original_title", "release_year",
                        "rating", "popularity_alltime", "popularity_1year", "popularity_1month",
                        "popularity_1week". Default is "original_title".
        order_direction (str): Sort direction. Options: "asc", "desc". Default is "asc".
        series_granularity (str): Output detail level. Options: "show", "season", "episode".
                                   Default is "show".
        toolbench_rapidapi_key (str): RapidAPI key.

    Returns:
        dict: JSON response containing matching shows with streaming availability.
    """
    conn = http.client.HTTPSConnection("streaming-availability.p.rapidapi.com")

    query_params = f"country={country}&order_by={order_by}&order_direction={order_direction}&series_granularity={series_granularity}"
    if catalogs:
        query_params += f"&catalogs={catalogs}"
    if show_type:
        query_params += f"&show_type={show_type}"
    if genres:
        query_params += f"&genres={genres}"
    if keyword:
        query_params += f"&keyword={keyword}"

    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "streaming-availability.p.rapidapi.com"
    }

    conn.request("GET", f"/shows/search/filters?{query_params}", headers=headers)
    res = conn.getresponse()
    data = res.read()
    conn.close()

    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data.decode("utf-8")}
