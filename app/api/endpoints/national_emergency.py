from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.endpoints.dependencies import get_db, get_current_user
from app.schemas.national_emergency import (
    EmergencyAlert,
    EmergencyAlertResponse,
    EmergencyAlertSubscription,
    EmergencyAlertRequest
)
from app.services.national_emergency_service import NationalEmergencyService
from app.db.models.user import User

router = APIRouter()

@router.get("/alerts", response_model=EmergencyAlertResponse)
async def get_alerts(
    latitude: float = Query(..., description="Latitude of the location"),
    longitude: float = Query(..., description="Longitude of the location"),
    radius_km: float = Query(10.0, description="Radius in kilometers to search for alerts"),
    alert_types: List[str] = Query(None, description="Types of alerts to include"),
    include_resources: bool = Query(True, description="Include nearby emergency resources"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get active emergency alerts for a location.
    """
    try:
        service = NationalEmergencyService(db)
        request = EmergencyAlertRequest(
            user_id=current_user.id,
            location={"latitude": latitude, "longitude": longitude},
            alert_types=alert_types,
            radius_km=radius_km,
            include_resources=include_resources
        )
        return await service.get_active_alerts(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
