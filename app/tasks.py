from celery import Celery
from app.services.notification_service import send_notification

celery = Celery(
    "background_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

@celery.task
def send_delayed_notification(user_id: int, message: str):
    """Send a notification with a delay."""
    send_notification(user_id, message)
