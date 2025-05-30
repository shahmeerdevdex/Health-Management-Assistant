from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.emergency_health_ids import (
    EmergencyHealthIDCreate,
    EmergencyHealthIDResponse,
    EmergencyHealthIDWallet
)
from app.services.emergency_health_service import EmergencyHealthService
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
    Includes QR code generation and lock-screen integration.
    """
    service = EmergencyHealthService(db)
    return await service.create_or_update_health_id(current_user.id, health_data)

@router.get("/health-id/{user_id}", response_model=EmergencyHealthIDResponse)
async def get_emergency_health_id_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve Emergency Health ID details for a user.
    Includes access tracking and QR code if enabled.
    """
    service = EmergencyHealthService(db)
    emergency_data = await service.get_health_id(user_id)
    if not emergency_data:
        raise HTTPException(status_code=404, detail="Emergency Health ID not found")
    return emergency_data

@router.get("/health-id/{user_id}/wallet", response_model=EmergencyHealthIDWallet)
async def get_emergency_health_wallet_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get Emergency Health ID in digital wallet format.
    Compatible with Apple Wallet and Google Pay.
    """
    service = EmergencyHealthService(db)
    wallet_data = await service.get_wallet_format(user_id)
    if not wallet_data:
        raise HTTPException(status_code=404, detail="Emergency Health ID not found")
    return wallet_data

@router.post("/health-id/{user_id}/lock-screen")
async def toggle_lock_screen_endpoint(
    user_id: int,
    enabled: bool,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Toggle lock screen integration for Emergency Health ID.
    When enabled, emergency information will be accessible from the device lock screen.
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this health ID")
    
    service = EmergencyHealthService(db)
    success = await service.toggle_lock_screen(user_id, enabled)
    if not success:
        raise HTTPException(status_code=404, detail="Emergency Health ID not found")
    
    return {"message": f"Lock screen integration {'enabled' if enabled else 'disabled'} successfully"}
