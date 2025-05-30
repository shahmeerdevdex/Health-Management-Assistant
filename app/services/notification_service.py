from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.notifications import Notification
import logging
from app.services.email_service import send_email
from app.services.sms_service import send_sms
from app.db.session import SessionLocal
from app.crud.notification import create_notification
from app.db.models.user import User

logger = logging.getLogger(__name__)

async def send_notification(
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
    priority: str = "normal",
    db: Optional[AsyncSession] = None
) -> Notification:
    """
    Send a notification to a user.
    
    Args:
        user_id: The ID of the user to send the notification to
        title: The title of the notification
        message: The message content
        notification_type: The type of notification (e.g., "health_alert", "health_insight")
        priority: The priority level ("low", "normal", "high")
        db: Optional database session. If not provided, notification will be logged only.
    
    Returns:
        The created notification if db is provided, None otherwise
    """
    try:
        # Log the notification
        logger.info(f"Sending {notification_type} notification to user {user_id}: {title} - {message}")
        
        # If database session is provided, create notification record
        if db:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                created_at=datetime.utcnow(),
                is_read=False
            )
            db.add(notification)
            await db.commit()
            await db.refresh(notification)
            return notification
        
        return None
        
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return None

async def send_notification_via_email_and_sms(user_id: int, message: str):
    """Send a notification via email and SMS."""
    db = SessionLocal()
    
    # Fetch user contact details
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.error(f"User {user_id} not found.")
        return await False

    email_sent = send_email(user.email, "Health Notification", message)
    sms_sent = send_sms(user.phone, message)

    # Save notification in the database
    create_notification(db, user_id, message)

    if email_sent or sms_sent:
        logger.info(f"Notification sent to user {user_id}")
        return await True
    else:
        logger.error(f"Failed to send notification to user {user_id}")
        return await False
