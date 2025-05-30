from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.endpoints.dependencies import get_current_user, get_db
from app.schemas.ehr_sync import (
    EHRConnectionCreate,
    EHRConnectionUpdate,
    EHRConnectionInDB,
    WebhookEvent,
    SyncResponse,
    SyncStatus,
    EHRSyncRequest,
    EHRSyncResponse,
    EHRConnectionConfig,
    EHRConnectionStatus,
    EHRSystem,
    NationalDatabaseType,
    FHIRResource,
    FHIRResourceType
)
from app.services.realtime_sync import RealtimeSyncService
from app.services.data_mapping_service import DataMappingService
from app.services.ehr_sync import EHRService
from app.core.config import settings
from app.db.models.user import User, UserRoleInput
from app.crud.ehr_sync import EHRSyncCRUD
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Connection Management Endpoints
@router.post("/connect")
async def connect_ehr_system(
    user_id: int,
    config: EHRConnectionConfig,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Connect to an EHR system."""
    try:
        ehr_service = EHRService(db)
        connection = await ehr_service.connect_ehr_system(user_id, config)
        
        return {
            "status": "success",
            "message": f"Successfully connected to {config.ehr_system}",
            "connection_id": connection.id,
            "ehr_system": connection.ehr_system,
            "is_active": connection.is_active
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.get("/connections", response_model=List[EHRConnectionInDB])
async def get_ehr_connections(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all EHR connections and linked provider credentials for the current user."""
    try:
        sync_service = RealtimeSyncService(db)
        connections = await sync_service.get_user_connections(current_user.id)
        return connections
    except Exception as e:
        logger.error(f"Error getting EHR connections: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/connections/{connection_id}", response_model=EHRConnectionInDB)
async def update_ehr_connection(
    *,
    db: AsyncSession = Depends(get_db),
    connection_id: int,
    connection_in: EHRConnectionUpdate,
    current_user = Depends(get_current_user)
):
    """Update an EHR connection or provider credentials."""
    try:
        sync_service = RealtimeSyncService(db)
        connection = await sync_service.update_connection(
            connection_id=connection_id,
            user_id=current_user.id,
            update_data=connection_in.dict(exclude_unset=True)
        )
        return connection
    except Exception as e:
        logger.error(f"Error updating EHR connection: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/disconnect/{ehr_system}")
async def disconnect_ehr_system(
    ehr_system: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Disconnect from an EHR system or unlink provider credentials."""
    try:
        ehr_service = EHRService(db)
        connection = await ehr_service._get_ehr_connection(current_user.id, ehr_system)
        
        if not connection:
            raise HTTPException(
                status_code=404,
                detail=f"No active connection found for {ehr_system}"
            )

        connection.is_active = False
        await db.commit()
        
        return {"message": f"Successfully disconnected from {ehr_system}"}
    except Exception as e:
        logger.error(f"Failed to disconnect from EHR system: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# FHIR Resource Endpoints
@router.get("/resources/{user_id}", response_model=List[FHIRResource])
async def get_fhir_resources(
    user_id: int,
    resource_type: Optional[FHIRResourceType] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get FHIR resources for a user."""
    if current_user.id != user_id and current_user.role not in [UserRoleInput.PRACTITIONER, UserRoleInput.ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this user's FHIR resources"
        )

    try:
        ehr_service = EHRService(db)
        resources = await ehr_service.get_cached_fhir_resources(
            user_id=user_id,
            resource_type=resource_type
        )
        return resources
    except Exception as e:
        logger.error(f"Failed to get FHIR resources: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Webhook Endpoint for EHR Systems
@router.post("/webhooks/ehr/{connection_id}")
async def ehr_webhook(
    *,
    db: AsyncSession = Depends(get_db),
    connection_id: int,
    event: WebhookEvent
):
    """Handle incoming webhook events from EHR systems."""
    try:
        sync_service = RealtimeSyncService(db)
        await sync_service.handle_webhook(connection_id, event.event_type, event.data)
        return {"message": "Webhook processed successfully"}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 