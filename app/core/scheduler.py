from celery import Celery
from datetime import datetime, timedelta
import asyncio
from app.db.session import SessionLocal
from app.services.automated_health_monitor import AutomatedHealthMonitor
from app.services.notification_service import send_notification
from app.services.report_service import generate_health_report
from app.services.ai_services import analyze_symptoms
from utils.send_sms import send_sms
from utils.send_email import send_email
from app.crud.health_diary import get_recent_entries
from app.crud.user import get_active_users
import logging

logger = logging.getLogger(__name__)

# Celery Configuration
celery = Celery(
    "health_monitor",
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
def run_health_analysis():
    """Run comprehensive health analysis for all users."""
    async def analyze_all_users():
        async with SessionLocal() as db:
            monitor = AutomatedHealthMonitor(db)
            users = await get_active_users()
            
            for user in users:
                try:
                    # Get health analysis
                    analysis = await monitor.analyze_health_patterns(user.id)
                    
                    # Check for high-risk conditions
                    if analysis.get('risk_factors'):
                        high_risk_factors = [f for f in analysis['risk_factors'] if f['severity'] == 'high']
                        if high_risk_factors:
                            await send_notification(
                                user_id=user.id,
                                title="Health Risk Alert",
                                message=f"High-risk factors detected: {', '.join(f['description'] for f in high_risk_factors)}",
                                notification_type="high_risk_alert"
                            )
                    
                    # Send recommendations if available
                    if analysis.get('recommendations'):
                        await send_notification(
                            user_id=user.id,
                            title="Health Recommendations",
                            message="New health recommendations available. Please check your dashboard.",
                            notification_type="health_recommendation"
                        )
                
                except Exception as e:
                    logger.error(f"Error analyzing health data for user {user.id}: {str(e)}")
    
    asyncio.run(analyze_all_users())


@celery.task
def check_high_risk_patients():
    """Check for high-risk patients and send alerts."""
    async def check_risks():
        async with SessionLocal() as db:
            monitor = AutomatedHealthMonitor(db)
            users = await get_active_users()
            
            for user in users:
                try:
                    risk_score, alerts = await monitor.check_health_status(user.id)
                    if risk_score >= 0.7:
                        await send_notification(
                            user_id=user.id,
                            title="Urgent Health Alert",
                            message=f"High risk detected (score: {risk_score:.2f}). Please check your health status.",
                            notification_type="urgent_health_alert"
                        )
                except Exception as e:
                    logger.error(f"Error checking health status for user {user.id}: {str(e)}")
    
    asyncio.run(check_risks())


@celery.task
def generate_weekly_health_report(user_id: int):
    """Generate weekly health report for a user."""
    async def generate_report():
        async with SessionLocal() as db:
            monitor = AutomatedHealthMonitor(db)
            try:
                # Get weekly analysis
                analysis = await monitor.analyze_health_patterns(user_id, days=7)
                
                # Generate report content
                report = {
                    "period": "weekly",
                    "start_date": (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d"),
                    "end_date": datetime.utcnow().strftime("%Y-%m-%d"),
                    "risk_factors": analysis.get('risk_factors', []),
                    "trends": analysis.get('trends', {}),
                    "recommendations": analysis.get('recommendations', [])
                }
                
                # Send report notification
                await send_notification(
                    user_id=user_id,
                    title="Weekly Health Report",
                    message="Your weekly health report is ready. Please check your dashboard.",
                    notification_type="health_report"
                )
                
                return report
            except Exception as e:
                logger.error(f"Error generating weekly report for user {user_id}: {str(e)}")
                return None
    
    return asyncio.run(generate_report())


# ---------------- Celery Beat Schedule ----------------

celery.conf.beat_schedule = {
    "daily_health_check_in": {
        "task": "app.core.scheduler.schedule_health_check_in",
        "schedule": timedelta(days=1),
    },
    "health_analysis": {
        "task": "app.core.scheduler.run_health_analysis",
        "schedule": timedelta(hours=6),  # Run every 6 hours
    },
    "check_high_risk_patients": {
        "task": "app.core.scheduler.check_high_risk_patients",
        "schedule": timedelta(minutes=30),  # Check every 30 minutes
    },
    "weekly_health_reports": {
        "task": "app.core.scheduler.generate_weekly_health_report",
        "schedule": timedelta(weeks=1),
        "args": [1],  # Replace with dynamic user ID logic
    }
}

# Optional CLI entrypoint
if __name__ == "__main__":
    celery.start()
