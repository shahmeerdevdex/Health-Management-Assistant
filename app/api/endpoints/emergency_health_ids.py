from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.emergency_health_ids import EmergencyHealthIDCreate, EmergencyHealthIDResponse
from app.crud.emergency_health import create_or_update_emergency_health, get_emergency_health_id
from app.api.endpoints.dependencies import get_current_user

router = APIRouter()

@router.post("/health-id", response_model=EmergencyHealthIDResponse)
async def create_or_update_emergency_health_endpoint(
    health_data: EmergencyHealthIDCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Create or update the Emergency Health ID for the authenticated user.
    """
    return await create_or_update_emergency_health(db, current_user.id, health_data)

@router.get("/health-id/{user_id}", response_model=EmergencyHealthIDResponse)
async def get_emergency_health_id_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve Emergency Health ID details for a user.
    """
    emergency_data = await get_emergency_health_id(db, user_id)
    if not emergency_data:
        raise HTTPException(status_code=404, detail="Emergency Health ID not found")

    return emergency_data
