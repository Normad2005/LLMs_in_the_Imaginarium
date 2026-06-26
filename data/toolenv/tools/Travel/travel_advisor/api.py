import http.client
import json
from urllib.parse import quote
from config.api_keys import RAPIDAPI_KEY


def get_restaurants_by_location(
    bl_latitude: float,
    tr_latitude: float,
    bl_longitude: float,
    tr_longitude: float,
    limit: int = 30,
    currency: str = "USD",
    offset: int = 0,
    lang: str = "en_US",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    Search for restaurants within a geographic area using GPS coordinates.
    First resolves the center coordinate to a TripAdvisor location_id,
    then retrieves restaurant listings for that location.

    Parameters:
        bl_latitude (float): Bottom-left (southwest) latitude of the search area. Required.
        tr_latitude (float): Top-right (northeast) latitude of the search area. Required.
        bl_longitude (float): Bottom-left (southwest) longitude of the search area. Required.
        tr_longitude (float): Top-right (northeast) longitude of the search area. Required.
        limit (int): Maximum number of restaurant results to return. Default is 30.
        currency (str): Currency code for price display (e.g., "USD", "EUR"). Default is "USD".
        offset (int): Pagination offset. Default is 0.
        lang (str): Language/locale code (e.g., "en_US", "zh_TW"). Default is "en_US".
        toolbench_rapidapi_key (str): RapidAPI key.

    Returns:
        dict: JSON response containing restaurant listings for the area.
    """
    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "travel-advisor.p.rapidapi.com"
    }

    # Step 1: Resolve center coordinate to city name, then get TripAdvisor location_id
    center_lat = (bl_latitude + tr_latitude) / 2
    center_lng = (bl_longitude + tr_longitude) / 2

    # Use Nominatim reverse geocoding to get city name
    import urllib.request
    try:
        nominatim_url = f"https://nominatim.openstreetmap.org/reverse?lat={center_lat}&lon={center_lng}&format=json"
        req = urllib.request.Request(nominatim_url, headers={"User-Agent": "toolbench/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            geo = json.loads(resp.read().decode("utf-8"))
        address = geo.get("address", {})
        city_name = (
            address.get("city") or address.get("town") or
            address.get("village") or address.get("county") or
            address.get("state") or geo.get("display_name", "").split(",")[0]
        )
    except Exception:
        city_name = f"{center_lat},{center_lng}"

    conn = http.client.HTTPSConnection("travel-advisor.p.rapidapi.com")
    conn.request(
        "GET",
        f"/locations/v2/auto-complete?query={quote(city_name)}&lang={lang}&units=km&currency={currency}",
        headers=headers
    )
    res = conn.getresponse()
    data = res.read()
    conn.close()

    try:
        location_data = json.loads(data.decode("utf-8"))
        results = (location_data.get("data", {})
                               .get("Typeahead_autocomplete", {})
                               .get("results", []))
        if not results:
            return {"error": "Could not resolve location", "response": location_data}
        # Prefer isGeo=True (region-level) location for better results
        geo_results = [r for r in results if r.get("detailsV2", {}).get("isGeo")]
        chosen = geo_results[0] if geo_results else results[0]
        location_id = chosen["detailsV2"]["locationId"]
    except Exception as e:
        return {"error": f"Location resolve failed: {e}", "raw": data.decode("utf-8")}

    # Step 2: Get restaurants for that location_id
    conn2 = http.client.HTTPSConnection("travel-advisor.p.rapidapi.com")
    conn2.request(
        "GET",
        f"/restaurants/list?location_id={location_id}&limit={limit}&currency={currency}&lang={lang}&offset={offset}",
        headers=headers
    )
    res2 = conn2.getresponse()
    data2 = res2.read()
    conn2.close()

    try:
        return json.loads(data2.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data2.decode("utf-8")}


def get_hotels_by_location(
    bl_latitude: float,
    tr_latitude: float,
    bl_longitude: float,
    tr_longitude: float,
    checkin: str,
    checkout: str,
    adults: int = 2,
    rooms: int = 1,
    limit: int = 30,
    currency: str = "USD",
    offset: int = 0,
    lang: str = "en_US",
    toolbench_rapidapi_key: str = RAPIDAPI_KEY
):
    """
    Search for hotels within a geographic area using GPS coordinates and travel dates.
    First resolves the center coordinate to a TripAdvisor location_id,
    then retrieves hotel listings for that location.

    Parameters:
        bl_latitude (float): Bottom-left (southwest) latitude of the search area. Required.
        tr_latitude (float): Top-right (northeast) latitude of the search area. Required.
        bl_longitude (float): Bottom-left (southwest) longitude of the search area. Required.
        tr_longitude (float): Top-right (northeast) longitude of the search area. Required.
        checkin (str): Check-in date in 'YYYY-MM-DD' format. Required.
        checkout (str): Check-out date in 'YYYY-MM-DD' format. Required.
        adults (int): Number of adult guests. Default is 2.
        rooms (int): Number of rooms required. Default is 1.
        limit (int): Maximum number of hotel results to return. Default is 30.
        currency (str): Currency code for price display (e.g., "USD", "EUR"). Default is "USD".
        offset (int): Pagination offset. Default is 0.
        lang (str): Language/locale code (e.g., "en_US", "zh_TW"). Default is "en_US".
        toolbench_rapidapi_key (str): RapidAPI key.

    Returns:
        dict: JSON response containing hotel listings for the area.
    """
    headers = {
        "x-rapidapi-key": toolbench_rapidapi_key,
        "x-rapidapi-host": "travel-advisor.p.rapidapi.com"
    }

    # Step 1: Resolve center coordinate to city name, then get TripAdvisor location_id
    center_lat = (bl_latitude + tr_latitude) / 2
    center_lng = (bl_longitude + tr_longitude) / 2

    # Use Nominatim reverse geocoding to get city name
    import urllib.request
    try:
        nominatim_url = (
            "https://nominatim.openstreetmap.org/reverse"
            "?lat=" + str(center_lat) + "&lon=" + str(center_lng) + "&format=json"
        )
        req = urllib.request.Request(nominatim_url, headers={"User-Agent": "toolbench/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            geo = json.loads(resp.read().decode("utf-8"))
        address = geo.get("address", {})
        city_name = (
            address.get("city") or address.get("town") or
            address.get("village") or address.get("county") or
            address.get("state") or geo.get("display_name", "").split(",")[0]
        )
    except Exception:
        city_name = str(center_lat) + "," + str(center_lng)

    conn = http.client.HTTPSConnection("travel-advisor.p.rapidapi.com")
    conn.request(
        "GET",
        "/locations/v2/auto-complete?query=" + quote(city_name) + "&lang=" + lang + "&units=km&currency=" + currency,
        headers=headers
    )
    res = conn.getresponse()
    data = res.read()
    conn.close()

    try:
        location_data = json.loads(data.decode("utf-8"))
        results = (location_data.get("data", {})
                               .get("Typeahead_autocomplete", {})
                               .get("results", []))
        if not results:
            return {"error": "Could not resolve location", "response": location_data}
        # Prefer isGeo=True (region-level) location for better results
        geo_results = [r for r in results if r.get("detailsV2", {}).get("isGeo")]
        chosen = geo_results[0] if geo_results else results[0]
        location_id = chosen["detailsV2"]["locationId"]
    except Exception as e:
        return {"error": f"Location resolve failed: {e}", "raw": data.decode("utf-8")}

    # Step 2: Get hotels for that location_id
    conn2 = http.client.HTTPSConnection("travel-advisor.p.rapidapi.com")
    conn2.request(
        "GET",
        f"/hotels/list?location_id={location_id}&checkin={checkin}&checkout={checkout}&adults={adults}&rooms={rooms}&limit={limit}&currency={currency}&lang={lang}&offset={offset}",
        headers=headers
    )
    res2 = conn2.getresponse()
    data2 = res2.read()
    conn2.close()

    try:
        return json.loads(data2.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON response", "raw": data2.decode("utf-8")}
