from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.crud.notification import (
    create_notification,
    get_notifications,
    delete_notification
)
from app.api.endpoints.dependencies import get_current_user  

router = APIRouter()

@router.post("/send", response_model=NotificationResponse)
async def send_notification_endpoint(
    notification: NotificationCreate, 
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)  
):
    """
    Send a notification.
    """
    new_notification = await create_notification(db, notification)

    if not new_notification:
        raise HTTPException(status_code=400, detail="Failed to send notification.")

    return new_notification 


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get all notifications for the authenticated user.
    """
    return await get_notifications(db, current_user.id)


@router.delete("/{notification_id}")
async def delete_notification_endpoint(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Delete a specific notification belonging to the authenticated user.
    """
    return await delete_notification(db, notification_id, current_user.id)
