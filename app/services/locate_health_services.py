import httpx
from app.core.config import settings
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from geopy.distance import geodesic

logger = logging.getLogger(__name__)

# Google Maps API configuration
GOOGLE_MAPS_API_KEY = settings.GOOGLE_MAPS_API_KEY
PLACES_API_BASE_URL = "https://maps.googleapis.com/maps/api/place"



async def get_nearby_health_services(
        lat: float,
        lon: float,
        radius: int = 5000,
        service_type: Optional[str] = None,
        availability: Optional[bool] = None,
        max_wait_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch nearby health services with advanced filtering and real-time data."""
        
        # Define health service types to search for
        health_types = ["hospital", "pharmacy", "doctor", "health"]
        if service_type:
            health_types = [service_type]
        
        results = []
        
        for place_type in health_types:
            # Search for places
            places = await _search_places(lat, lon, radius, place_type)
            
            # Get detailed information for each place
            for place in places:
                place_details = await _get_place_details(place["place_id"])
                if place_details:
                    # Get real-time availability and wait times
                    real_time_data = await _get_real_time_data(place_details)
                    
                    # Apply filters
                    if availability is not None and real_time_data["is_available"] != availability:
                        continue
                    if max_wait_time is not None and real_time_data["estimated_wait_time"] > max_wait_time:
                        continue
                    
                    results.append({
                        "name": place_details.get("name"),
                        "latitude": place_details.get("geometry", {}).get("location", {}).get("lat"),
                        "longitude": place_details.get("geometry", {}).get("location", {}).get("lng"),
                        "address": place_details.get("formatted_address"),
                        "rating": place_details.get("rating", "No rating"),
                        "category": place_type,
                        "phone": place_details.get("formatted_phone_number"),
                        "website": place_details.get("website"),
                        "opening_hours": place_details.get("opening_hours", {}).get("weekday_text", []),
                        "types": place_details.get("types", []),
                        "real_time_data": real_time_data,
                        "specialized_services": await _get_specialized_services(place_details),
                        "emergency_services": await _get_emergency_services(place_details),
                        "accessibility_info": await _get_accessibility_info(place_details)
                    })
        
        # Sort results by distance and wait time
        results.sort(key=lambda x: (
            geodesic((lat, lon), (x["latitude"], x["longitude"])).kilometers,
            x["real_time_data"]["estimated_wait_time"]
        ))
        
        return results

async def _search_places(lat: float, lon: float, radius: int, place_type: str) -> List[Dict[str, Any]]:
        """Search for places using Google Maps Places API."""
        url = f"{PLACES_API_BASE_URL}/nearbysearch/json"
        params = {
            "location": f"{lat},{lon}",
            "radius": radius,
            "type": place_type,
            "key": GOOGLE_MAPS_API_KEY
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if data.get("status") == "OK":
                return data.get("results", [])
            return []

async def _get_place_details(place_id: str) -> Dict[str, Any]:
        """Get detailed information about a place using Google Maps Places API."""
        url = f"{PLACES_API_BASE_URL}/details/json"
        params = {
            "place_id": place_id,
            "fields": "name,formatted_address,geometry,rating,formatted_phone_number,website,opening_hours,types",
            "key": GOOGLE_MAPS_API_KEY
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if data.get("status") == "OK":
                return data.get("result", {})
            return {}

async def _get_real_time_data(place_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get real-time availability and wait time data for a facility."""
        # This would typically integrate with the facility's real-time system
        # For now, returning mock data
        return {
            "is_available": True,
            "estimated_wait_time": 30,  # minutes
            "current_capacity": "moderate",
            "last_updated": datetime.utcnow().isoformat()
        }

async def _get_specialized_services(place_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get specialized services offered by the facility."""
        # This would typically come from a database of facility services
        # For now, returning mock data
        return [
            {
                "name": "Trauma Center",
                "level": "Level 1",
                "available": True
            },
            {
                "name": "Stroke Center",
                "certification": "Advanced",
                "available": True
            }
        ]

async def _get_emergency_services(place_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get emergency service capabilities of the facility."""
        # This would typically come from a database of emergency services
        # For now, returning mock data
        return {
            "emergency_department": True,
            "trauma_center": True,
            "stroke_center": True,
            "cardiac_care": True,
            "pediatric_emergency": True,
            "24_hour_service": True
        }

async def _get_accessibility_info(place_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get accessibility information for the facility."""
        # This would typically come from a database of accessibility information
        # For now, returning mock data
        return {
            "wheelchair_accessible": True,
            "accessible_parking": True,
            "accessible_entrance": True,
            "accessible_restrooms": True,
            "sign_language_available": True,
            "braille_available": True
        }

async def get_route_to_facility(
        start_lat: float,
        start_lon: float,
        facility_lat: float,
        facility_lon: float,
        mode: str = "driving"
    ) -> Dict[str, Any]:
        """Get optimized route to a health facility."""
        if not GOOGLE_MAPS_API_KEY:
            raise ValueError("Google Maps API key is not configured")
            
        if mode not in ["driving", "walking", "transit"]:
            raise ValueError("Invalid travel mode. Must be one of: driving, walking, transit")
            
        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": f"{start_lat},{start_lon}",
            "destination": f"{facility_lat},{facility_lon}",
            "mode": mode,
            "key": GOOGLE_MAPS_API_KEY
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                data = response.json()
                
                if data.get("status") == "OK" and data.get("routes"):
                    route = data["routes"][0]
                    return {
                        "distance": route["legs"][0]["distance"]["text"],
                        "duration": route["legs"][0]["duration"]["text"],
                        "steps": route["legs"][0]["steps"],
                        "polyline": route["overview_polyline"]["points"]
                    }
                elif data.get("status") == "ZERO_RESULTS":
                    return {"error": "No route found between the specified locations"}
                elif data.get("status") == "INVALID_REQUEST":
                    return {"error": "Invalid request parameters"}
                elif data.get("status") == "REQUEST_DENIED":
                    return {"error": "Request denied. Please check API key configuration"}
                else:
                    return {"error": f"Google Maps API error: {data.get('status')}"}
        except httpx.RequestError as e:
            logger.error(f"Error making request to Google Maps API: {str(e)}")
            return {"error": "Failed to connect to Google Maps API"}
        except Exception as e:
            logger.error(f"Unexpected error in get_route_to_facility: {str(e)}")
            return {"error": "An unexpected error occurred"}

async def get_facility_availability(
        facility_id: str,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get facility availability for a specific date."""
        # This would typically integrate with the facility's scheduling system
        # For now, returning mock data
        return {
            "date": date or datetime.utcnow(),
            "available_slots": [
                {"time": "09:00", "type": "general"},
                {"time": "10:30", "type": "specialist"},
                {"time": "14:00", "type": "emergency"}
            ],
            "capacity": {
                "total": 100,
                "available": 75,
                "reserved": 25
            }
        }

async def reverse_geocode_google(latitude: float, longitude: float) -> str:
    """Convert latitude & longitude to a readable address using Google Maps Geocoding API."""
    if not latitude or not longitude:
        return "Unknown location"
    
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "latlng": f"{latitude},{longitude}",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        
        if data.get("status") == "OK" and data.get("results"):
            return data["results"][0]["formatted_address"]
        return "Unknown location"