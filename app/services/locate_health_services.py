import httpx
from app.core.config import settings


# SERPAPI_KEY = settings.SERPAPI_KEY
# MAPBOX_ACCESS_TOKEN = settings.MAPBOX_ACCESS_TOKEN

async def get_nearby_health_services(lat: float, lon: float, radius: int = 5000):
    """Fetch nearby health services (hospitals, pharmacies, clinics) using SerpApi."""
    
    search_query = "hospitals, pharmacies, clinics near me"
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_maps",
        "q": search_query,
        "ll": f"@{lat},{lon},15z",  # Location in lat/lng format
        "type": "search",
        # "api_key": SERPAPI_KEY
    }

    results = []
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()

    if "local_results" in data:
        for place in data["local_results"]:
            lat_lng = place.get("gps_coordinates", {})
            results.append({
                "name": place.get("title"),
                "latitude": lat_lng.get("latitude"),
                "longitude": lat_lng.get("longitude"),
                "address": await reverse_geocode_mapbox(lat_lng.get("latitude"), lat_lng.get("longitude")),
                "rating": place.get("rating", "No rating"),
                "category": place.get("type", "health")
            })
    
    return results

async def reverse_geocode_mapbox(latitude, longitude):
    """Convert latitude & longitude to a readable address using Mapbox."""
    if not latitude or not longitude:
        return "Unknown location"
    
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{longitude},{latitude}.json"
    params = {"access_token": MAPBOX_ACCESS_TOKEN}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()

    return data["features"][0]["place_name"] if data.get("features") else "Unknown location"