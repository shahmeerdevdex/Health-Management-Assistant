from celery import Celery
from datetime import timedelta
import asyncio
from app.services.notification_service import send_notification
from app.services.report_service import generate_health_report
from app.services.ai_services import analyze_symptoms
from utils.send_sms import send_sms
from utils.send_email import send_email
from app.crud.health_diary import get_recent_entries
from app.crud.user import get_active_users

# Celery Configuration
celery = Celery(
    "health_scheduler",
    broker="redis://localhost:6379/0",  
    backend="redis://localhost:6379/0",  
)

celery.conf.timezone = "UTC"

CRITICAL_SYMPTOMS = {"chest pain", "shortness of breath", "fainting"}


# ---------------- Celery Tasks ----------------

@celery.task
def send_medication_reminders(user_id: int):
    """Send scheduled medication reminders to users."""
    asyncio.run(send_notification(user_id, "It's time to take your medication!"))


@celery.task
def schedule_health_check_in():
    """Send AI-driven symptom check-in reminders to all users."""
    users = asyncio.run(get_active_users())
    for user in users:
        asyncio.run(send_notification(user.id, "Remember to log your daily health check-in!"))


@celery.task
def generate_weekly_health_report(user_id: int):
    """Generate and notify users of weekly health reports."""
    report_path = asyncio.run(generate_health_report(user_id))
    asyncio.run(send_notification(user_id, f"Your weekly health report is ready: {report_path}"))


@celery.task
def analyze_user_health_patterns():
    """Run AI-driven health pattern analysis."""
    users = asyncio.run(get_active_users())
    for user in users:
        asyncio.run(analyze_symptoms(user.id))


@celery.task
def run_high_risk_check():
    """Check health diary for critical symptoms or mood and send alerts."""
    asyncio.run(_check_for_high_risk_users())


async def _check_for_high_risk_users():
    recent_entries = await get_recent_entries(hours=24)

    for entry in recent_entries:
        flagged = any(symptom.lower() in CRITICAL_SYMPTOMS for symptom in entry.symptoms)
        if flagged or entry.mood_score <= 2:
            if entry.user.phone:
                await send_sms(entry.user.phone, "High-risk symptom detected")
            if entry.user.email:
                await send_email(
                    entry.user.email,
                    "Urgent Check-In Required",
                    "We've detected severe symptoms in your recent health diary entry."
                )


# ---------------- Celery Beat Schedule ----------------

celery.conf.beat_schedule = {
    "daily_health_check_in": {
        "task": "app.core.scheduler.schedule_health_check_in",
        "schedule": timedelta(days=1),
    },
    "weekly_report_generation": {
        "task": "app.core.scheduler.generate_weekly_health_report",
        "schedule": timedelta(weeks=1),
        "args": [1],  # Replace with dynamic user ID logic if needed
    },
    "ai_health_analysis": {
        "task": "app.core.scheduler.analyze_user_health_patterns",
        "schedule": timedelta(days=3),
    },
    "check_high_risk_users": {
        "task": "app.core.scheduler.run_high_risk_check",
        "schedule": timedelta(minutes=30),
    },
}

# Optional CLI entrypoint
if __name__ == "__main__":
    celery.start()
