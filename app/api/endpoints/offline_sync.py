from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.offline_sync_service import OfflineSyncService
from app.api.endpoints.dependencies import get_current_user
from typing import Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/offline/store")
async def store_offline_data(
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Store data for offline access.
    This endpoint is used when the app is offline to store data locally.
    """
    try:
        service = OfflineSyncService(db)
        await service.store_offline_data(current_user.id, data)
        return {"message": "Data stored successfully for offline access"}
    except Exception as e:
        logger.error(f"Failed to store offline data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/offline/data")
async def get_offline_data(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Retrieve offline data for the current user.
    This endpoint is used to get locally stored data when offline.
    """
    try:
        service = OfflineSyncService(db)
        data = await service.get_offline_data(current_user.id)
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No offline data found"
            )
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get offline data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/offline/sync")
async def sync_offline_data(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Sync offline data with the server.
    This endpoint is called when the app comes back online to sync local changes.
    """
    try:
        service = OfflineSyncService(db)
        success = await service.sync_offline_data(current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to sync offline data"
            )
        return {"message": "Offline data synced successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync offline data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/offline/status")
async def get_sync_status(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get the sync status for the current user.
    This endpoint provides information about offline data and sync status.
    """
    try:
        service = OfflineSyncService(db)
        status = await service.get_sync_status(current_user.id)
        return status
    except Exception as e:
        logger.error(f"Failed to get sync status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 