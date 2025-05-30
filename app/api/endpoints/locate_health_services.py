from fastapi import APIRouter, HTTPException, Depends, Query
from app.services.locate_health_services import(
    get_nearby_health_services,get_facility_availability,
    get_route_to_facility,_get_accessibility_info,
    _get_emergency_services,_get_place_details,
    _get_real_time_data,_get_specialized_services,
    reverse_geocode_google
)
from app.schemas.locate_health_services import HealthServiceRequest, HealthServiceResponse
from app.api.endpoints.dependencies import get_current_user
from typing import Optional
from datetime import datetime

router = APIRouter()

@router.post("/nearby", response_model=list[HealthServiceResponse])
async def find_nearby_health_services(
    request: HealthServiceRequest,
    service_type: Optional[str] = Query(None, description="Type of health service to search for"),
    availability: Optional[bool] = Query(None, description="Filter by current availability"),
    max_wait_time: Optional[int] = Query(None, description="Maximum acceptable wait time in minutes"),
    db_user=Depends(get_current_user)
):
    """API endpoint to get nearby hospitals, clinics, and pharmacies with advanced filtering."""
    try:
        results = await get_nearby_health_services(
            lat=request.latitude,
            lon=request.longitude,
            radius=request.radius,
            service_type=service_type,
            availability=availability,
            max_wait_time=max_wait_time
        )
        if not results:
            raise HTTPException(status_code=404, detail="No health services found nearby.")
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/route")
async def get_route_to_facility(
    start_lat: float = Query(..., description="Starting latitude"),
    start_lon: float = Query(..., description="Starting longitude"),
    facility_lat: float = Query(..., description="Facility latitude"),
    facility_lon: float = Query(..., description="Facility longitude"),
    mode: str = Query("driving", description="Travel mode (driving, walking, transit)"),
    db_user=Depends(get_current_user)
):
    """Get optimized route to a health facility."""
    try:
        route = await get_route_to_facility(
            start_lat=start_lat,
            start_lon=start_lon,
            facility_lat=facility_lat,
            facility_lon=facility_lon,
            mode=mode
        )
        
        if "error" in route:
            if "No route found" in route["error"]:
                raise HTTPException(status_code=404, detail=route["error"])
            elif "Invalid request" in route["error"]:
                raise HTTPException(status_code=400, detail=route["error"])
            elif "API key" in route["error"]:
                raise HTTPException(status_code=500, detail="Google Maps API configuration error")
            else:
                raise HTTPException(status_code=500, detail=route["error"])
                
        return route
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/availability/{facility_id}")
async def get_facility_availability(
    facility_id: str,
    date: Optional[datetime] = Query(None, description="Date to check availability for"),
    db_user=Depends(get_current_user)
):
    """Get facility availability and scheduling information."""
    try:
        availability = await get_facility_availability(
            facility_id=facility_id,
            date=date
        )
        if not availability:
            raise HTTPException(status_code=404, detail="Facility availability information not found.")
        return availability
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
