from datetime import datetime, timedelta
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.services.health_checkin_service import get_pending_checkins, update_checkin_schedule
from app.services.notification_service import send_notification
from app.db.models.health_checkin import HealthCheckIn
import logging
from sqlalchemy import select

logger = logging.getLogger(__name__)

async def process_pending_checkins():
    """
    Background task to process pending health check-ins and send reminders.
    """
    while True:
        try:
            async with SessionLocal() as db:
                # Get all pending check-ins
                pending_checkins = await get_pending_checkins(db)
                
                for schedule in pending_checkins:
                    # Send reminder notification
                    await send_notification(
                        user_id=schedule.user_id,
                        title="Health Check-in Reminder",
                        message="It's time for your scheduled health check-in. Please update your health metrics.",
                        notification_type="checkin_reminder"
                    )
                    
                    # Update schedule
                    await update_checkin_schedule(
                        db=db,
                        schedule_id=schedule.id,
                        last_check_in=datetime.utcnow()
                    )
                    
                    logger.info(f"Sent check-in reminder to user {schedule.user_id}")
                
                await db.commit()
        
        except Exception as e:
            logger.error(f"Error in process_pending_checkins: {str(e)}")
        
        # Wait for 1 hour before next check
        await asyncio.sleep(3600)

async def check_high_risk_patients():
    """
    Background task to check for high-risk patients and send alerts.
    """
    while True:
        try:
            async with SessionLocal() as db:
                # Get all check-ins from the last 24 hours with high risk scores
                result = await db.execute(
                    select(HealthCheckIn)
                    .where(
                        HealthCheckIn.check_in_time >= datetime.utcnow() - timedelta(days=1),
                        HealthCheckIn.risk_score >= 0.7,
                        HealthCheckIn.notification_sent == False
                    )
                )
                high_risk_checkins = result.scalars().all()
                
                for checkin in high_risk_checkins:
                    # Send high-risk alert
                    await send_notification(
                        user_id=checkin.user_id,
                        title="High Risk Health Alert",
                        message=f"High risk detected: {checkin.attention_reason}. Please consult a healthcare provider.",
                        notification_type="high_risk_alert"
                    )
                    
                    # Mark notification as sent
                    checkin.notification_sent = True
                    checkin.notification_time = datetime.utcnow()
                    
                    logger.info(f"Sent high-risk alert to user {checkin.user_id}")
                
                await db.commit()
        
        except Exception as e:
            logger.error(f"Error in check_high_risk_patients: {str(e)}")
        
        # Check every 30 minutes
        await asyncio.sleep(1800)

async def start_health_checkin_tasks():
    """
    Start all health check-in related background tasks.
    """
    tasks = [
        asyncio.create_task(process_pending_checkins()),
        asyncio.create_task(check_high_risk_patients())
    ]
    
    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f"Error in health check-in tasks: {str(e)}")
        # Restart tasks if they fail
        await start_health_checkin_tasks() 