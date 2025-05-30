from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.endpoints.dependencies import get_db, get_current_user
from app.services.location_health_alerts import LocationHealthAlertService
from app.db.models.user import User
from typing import Optional

router = APIRouter()

@router.get("/alerts")
async def get_location_health_alerts(
    latitude: float = Query(..., description="Latitude of the location"),
    longitude: float = Query(..., description="Longitude of the location"),
    radius_km: float = Query(10.0, description="Radius in kilometers to search for alerts"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive health alerts for a location.
    Includes environmental, disease, personal health, facility, and emergency alerts.
    """
    try:
        service = LocationHealthAlertService(db)
        user_id = current_user.id if current_user else None
        alerts = await service.get_location_health_alerts(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            user_id=user_id
        )
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 