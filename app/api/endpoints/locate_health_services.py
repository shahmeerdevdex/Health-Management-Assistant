from fastapi import APIRouter, HTTPException,Depends
from app.services.locate_health_services import get_nearby_health_services  
from app.schemas.locate_health_services import HealthServiceRequest, HealthServiceResponse
from app.api.endpoints.dependencies import get_current_user
router = APIRouter()

@router.post("/nearby", response_model=list[HealthServiceResponse])
async def find_nearby_health_services(request: HealthServiceRequest, db_user=Depends(get_current_user)):
    """API endpoint to get nearby hospitals, clinics, and pharmacies."""
    try:
        results = await get_nearby_health_services(request.latitude, request.longitude, request.radius)
        if not results:
            raise HTTPException(status_code=404, detail="No health services found nearby.")
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
