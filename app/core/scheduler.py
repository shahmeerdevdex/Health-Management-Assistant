from celery import Celery
from datetime import datetime, timedelta
import asyncio

from app.core.config import settings
from app.services.notification_service import send_notification
from app.services.report_service import generate_health_report
from app.services.ai_service import analyze_symptoms
from app.crud.user import get_active_users

# Celery Configuration
celery = Celery(
    "health_scheduler",
    broker="redis://localhost:6379/0",  
    backend="redis://localhost:6379/0",  
)

celery.conf.timezone = "UTC"

# --- TASKS ---

@celery.task
def send_medication_reminders(user_id: int):
    """Send scheduled medication reminders to users."""
    asyncio.run(send_notification(user_id, "It's time to take your medication!"))


@celery.task
def schedule_health_check_in():
    """Send AI-driven symptom check-in reminders."""
    users = asyncio.run(get_active_users())  
    for user in users:
        asyncio.run(send_notification(user.id, "Remember to log your daily health check-in!"))


@celery.task
def generate_weekly_health_report(user_id: int):
    """Generate weekly health reports for users."""
    report_path = asyncio.run(generate_health_report(user_id))  
    asyncio.run(send_notification(user_id, f"Your weekly health report is ready: {report_path}"))


@celery.task
def analyze_user_health_patterns():
    """Run AI-driven health pattern analysis for symptom tracking."""
    users = asyncio.run(get_active_users())  
    for user in users:
        asyncio.run(analyze_symptoms(user.id)) 


# --- PERIODIC TASK SCHEDULE ---
celery.conf.beat_schedule = {
    "daily_health_check_in": {
        "task": "scheduler.schedule_health_check_in",
        "schedule": timedelta(days=1),
    },
    "weekly_report_generation": {
        "task": "scheduler.generate_weekly_health_report",
        "schedule": timedelta(weeks=1),
    },
    "ai_health_analysis": {
        "task": "scheduler.analyze_user_health_patterns",
        "schedule": timedelta(days=3),
    },
}

if __name__ == "__main__":
    celery.start()
