from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from datetime import datetime
from app.api.endpoints.dependencies import get_db, get_current_user
from app.schemas.emergency_response import (
    EmergencyResponseCreate,
    EmergencyResponseResponse,
    EmergencyResourceCreate,
    EmergencyResourceResponse,
    EmergencyProtocolCreate,
    EmergencyProtocolResponse,
    EmergencyTrainingCreate,
    EmergencyTrainingResponse,
    EmergencyResourceBase,
    EmergencyResponseCreate as EmergencyResponseSchema,
    EmergencyTeamCreate,
    EmergencyTeamResponse,
    EmergencyZoneCreate,
    EmergencyZoneResponse,
    EmergencyDispatchCreate,
    EmergencyDispatchResponse,
    EmergencyTrackingCreate,
    EmergencyTrackingResponse,
    EmergencyResourceInventoryCreate,
    EmergencyResourceInventoryResponse,
    EmergencyAnalytics,
    EmergencyResponseUpdate
)
from app.services.emergency_response_service import (
    create_emergency_response,
    get_emergency_response,
    update_emergency_response,
    get_nearby_resources,
    process_emergency_request,
    create_emergency_resource,
    create_emergency_protocol,
    create_emergency_training
)
from app.services.advanced_emergency_service import AdvancedEmergencyService
from app.db.models.user import User, UserRoleInput

router = APIRouter()

@router.post("/request", response_model=EmergencyResponseResponse)
async def create_emergency_request(
    request: EmergencyResponseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new emergency request and initiate response."""
    if request.user_id != current_user.id and current_user.role != UserRoleInput.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to create emergency request for another user")
    
    try:
        response = await process_emergency_request(db, request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/response/{response_id}", response_model=EmergencyResponseResponse)
async def get_response(
    response_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get emergency response details."""
    response = await get_emergency_response(db, response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Emergency response not found")
    
    if response.user_id != current_user.id and current_user.role not in [UserRoleInput.ADMIN, UserRoleInput.PRACTITIONER]:
        raise HTTPException(status_code=403, detail="Not authorized to view this emergency response")
    
    return response

@router.put("/response/{response_id}", response_model=EmergencyResponseResponse)
async def update_response(
    response_id: int,
    update_data: EmergencyResponseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update emergency response status and details.
    
    Allowed update fields:
    - status: Current status of the emergency (initialized, in_progress, resolved)
    - description: Updated description of the emergency
    - location_lat: Updated latitude of the emergency location
    - location_lon: Updated longitude of the emergency location
    - severity: Updated severity level of the emergency
    
    Example request body:
    ```json
    {
        "status": "in_progress",
        "description": "Updated description of the emergency",
        "severity": "high"
    }
    ```
    """
    # Get the emergency response first
    response = await get_emergency_response(db, response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Emergency response not found")
    
    # Allow update if user is admin, practitioner, or the owner of the response
    if (current_user.role not in [UserRoleInput.ADMIN, UserRoleInput.PRACTITIONER] and 
        response.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to update this emergency response")
    
    # Convert update_data to dict and remove None values
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    
    response = await update_emergency_response(db, response_id, update_dict)
    return response

@router.get("/resources/nearby", response_model=List[EmergencyResourceResponse])
async def get_resources(
    lat: float,
    lon: float,
    radius_km: float = 10.0,
    resource_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get nearby emergency resources."""
    resources = await get_nearby_resources(db, lat, lon, radius_km, resource_type)
    return resources

@router.post("/resources", response_model=EmergencyResourceResponse)
async def create_resource(
    resource_data: EmergencyResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new emergency resource."""
    if current_user.role != UserRoleInput.ADMIN:
        raise HTTPException(status_code=403, detail="Only administrators can create emergency resources")
    
    try:
        resource = await create_emergency_resource(db, resource_data)
        return resource
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/protocols", response_model=EmergencyProtocolResponse)
async def create_protocol(
    protocol_data: EmergencyProtocolCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new emergency protocol."""
    if current_user.role != UserRoleInput.ADMIN:
        raise HTTPException(status_code=403, detail="Only administrators can create emergency protocols")
    
    try:
        protocol = await create_emergency_protocol(db, protocol_data)
        return protocol
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/training", response_model=EmergencyTrainingResponse)
async def create_training(
    training_data: EmergencyTrainingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new emergency training record."""
    if training_data.user_id != current_user.id and current_user.role != UserRoleInput.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to create training record for another user")
    
    try:
        training = await create_emergency_training(db, training_data)
        return training
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/zones", response_model=EmergencyZoneResponse)
async def create_emergency_zone(
    zone_data: EmergencyZoneCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new emergency zone with specific protocols."""
    if current_user.role != UserRoleInput.ADMIN:
        raise HTTPException(status_code=403, detail="Only administrators can create emergency zones")
    
    service = AdvancedEmergencyService(db)
    try:
        zone = await service.create_emergency_zone(zone_data)
        return zone
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/dispatch", response_model=EmergencyDispatchResponse)
async def create_emergency_dispatch(
    dispatch_data: EmergencyDispatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new emergency dispatch record."""
    if current_user.role not in [UserRoleInput.ADMIN, UserRoleInput.PRACTITIONER]:
        raise HTTPException(status_code=403, detail="Not authorized to create dispatches")
    
    service = AdvancedEmergencyService(db)
    try:
        dispatch = await service.create_emergency_dispatch(dispatch_data)
        return dispatch
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tracking", response_model=EmergencyTrackingResponse)
async def update_emergency_tracking(
    tracking_data: EmergencyTrackingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update emergency tracking information."""
    if current_user.role not in [UserRoleInput.ADMIN, UserRoleInput.PRACTITIONER]:
        raise HTTPException(status_code=403, detail="Not authorized to update tracking")
    
    service = AdvancedEmergencyService(db)
    try:
        tracking = await service.update_emergency_tracking(tracking_data.emergency_id, tracking_data)
        return tracking
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inventory", response_model=EmergencyResourceInventoryResponse)
async def create_resource_inventory(
    inventory_data: EmergencyResourceInventoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new emergency resource inventory record."""
    if current_user.role != UserRoleInput.ADMIN:
        raise HTTPException(status_code=403, detail="Only administrators can manage inventory")
    
    service = AdvancedEmergencyService(db)
    try:
        inventory = await service.create_resource_inventory(inventory_data)
        return inventory
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics", response_model=EmergencyAnalytics)
async def get_emergency_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive emergency response analytics."""
    if current_user.role != UserRoleInput.ADMIN:
        raise HTTPException(status_code=403, detail="Only administrators can access analytics")
    
    service = AdvancedEmergencyService(db)
    try:
        analytics = await service.get_emergency_analytics()
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time emergency updates."""
    service = AdvancedEmergencyService(db)
    await service.connect_websocket(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            await service.handle_websocket_message(user_id, data)
    except Exception as e:
        await service.disconnect_websocket(user_id)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/start")
async def start_emergency_sync(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start real-time synchronization of emergency data."""
    if current_user.role not in [UserRoleInput.ADMIN, UserRoleInput.PRACTITIONER]:
        raise HTTPException(status_code=403, detail="Not authorized to start sync")
    
    service = AdvancedEmergencyService(db)
    try:
        await service.initialize_emergency_system()
        return {"message": "Emergency system synchronization started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync/status")
async def get_sync_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current synchronization status."""
    if current_user.role not in [UserRoleInput.ADMIN, UserRoleInput.PRACTITIONER]:
        raise HTTPException(status_code=403, detail="Not authorized to check sync status")
    
    service = AdvancedEmergencyService(db)
    try:
        status = await service.get_sync_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 