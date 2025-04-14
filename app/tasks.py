from celery import Celery
import asyncio

from app.services.notification_service import send_notification
from app.crud.health_diary import get_recent_entries
from app.services.sms_service import send_sms_alert
from app.services.email_service import send_email_alert

celery = Celery(
    "background_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

CRITICAL_SYMPTOMS = {"chest pain", "shortness of breath", "fainting"}

@celery.task
def send_delayed_notification(user_id: int, message: str):
    """Run sync wrapper for async notification send"""
    asyncio.run(_send_delayed_notification(user_id, message))


async def _send_delayed_notification(user_id: int, message: str):
    await send_notification(user_id, message)


@celery.task
def run_high_risk_check():
    """Wrapper to run the async high-risk checker from Celery"""
    asyncio.run(_check_for_high_risk_users())


async def _check_for_high_risk_users():
    recent_entries = await get_recent_entries(hours=24)

    for entry in recent_entries:
        flagged = any(symptom.lower() in CRITICAL_SYMPTOMS for symptom in entry.symptoms)
        if flagged or entry.mood_score <= 2:
            if entry.user.phone:
                await send_sms_alert(entry.user.phone, "High-risk symptom detected")
            if entry.user.email:
                await send_email_alert(
                    entry.user.email,
                    "Urgent Check-In Required",
                    "We've detected severe symptoms in your recent health diary entry."
                )
