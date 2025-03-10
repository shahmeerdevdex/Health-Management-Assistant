import logging
from app.services.email_service import send_email
from app.services.sms_service import send_sms
from app.db.session import SessionLocal
from app.crud.notification import create_notification
from app.db.models.user import User

logger = logging.getLogger("notification_service")

async def send_notification(user_id: int, message: str):
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
