from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.db.models.notifications import Notification
from app.db.models.user import User  
from app.schemas.notification import NotificationCreate
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import delete

async def create_notification(db: AsyncSession, notification: NotificationCreate):
  
    result = await db.execute(select(User).filter(User.id == notification.user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=400, detail=f"User with ID {notification.user_id} does not exist.")

    db_notification = Notification(
        user_id=notification.user_id,
        message=notification.message,
        sent_at=datetime.utcnow().replace(tzinfo=None)  
    )

    db.add(db_notification)
    try:
        await db.commit()
        await db.refresh(db_notification)
        return db_notification
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error inserting notification. Possible constraint violation.")

async def get_notifications(db: AsyncSession, user_id: int):
    """
    Retrieve all notifications for a specific user.
    """
    result = await db.execute(
        select(Notification).where(Notification.user_id == user_id)
    )
    return result.scalars().all()


async def delete_notification(db: AsyncSession, notification_id: int, user_id: int):
    """
    Delete a notification by its ID and user ID for ownership validation.
    """
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
    )
    notification = result.scalars().first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found or access denied")

    await db.delete(notification)
    await db.commit()

    return {"detail": "Notification deleted successfully"}
