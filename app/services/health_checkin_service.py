from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.health_checkin import HealthCheckIn, HealthCheckInSchedule
from app.schemas.health_checkin import HealthCheckInCreate, HealthMetrics
from app.services.notification_service import send_notification
import logging
from app.services.ai_services import  PredictiveHealthAnalytics
from sqlalchemy import select


logger = logging.getLogger(__name__)

predictive_analytics = PredictiveHealthAnalytics()

async def calculate_risk_score(metrics: HealthMetrics) -> tuple[float, Optional[str]]:
    """
    Calculate risk score based on health metrics and return attention reason if needed.
    """
    risk_score = 0.0
    attention_reason = None

    # Heart rate check
    if metrics.heart_rate:
        if metrics.heart_rate > 100:
            risk_score += 0.3
            attention_reason = "Elevated heart rate detected"
        elif metrics.heart_rate < 60:
            risk_score += 0.2
            attention_reason = "Low heart rate detected"

    # Blood pressure check
    if metrics.blood_pressure:
        systolic = metrics.blood_pressure.get("systolic")
        diastolic = metrics.blood_pressure.get("diastolic")
        if systolic and diastolic:
            if systolic > 140 or diastolic > 90:
                risk_score += 0.4
                attention_reason = "High blood pressure detected"
            elif systolic < 90 or diastolic < 60:
                risk_score += 0.3
                attention_reason = "Low blood pressure detected"

    # Blood sugar check
    if metrics.blood_sugar:
        if metrics.blood_sugar > 180:
            risk_score += 0.4
            attention_reason = "High blood sugar detected"
        elif metrics.blood_sugar < 70:
            risk_score += 0.5
            attention_reason = "Low blood sugar detected"

    # Temperature check
    if metrics.temperature:
        if metrics.temperature > 37.5:
            risk_score += 0.4
            attention_reason = "Elevated temperature detected"

    # Mood and stress check
    if metrics.mood and metrics.stress_level:
        if metrics.mood <= 2 or metrics.stress_level >= 4:
            risk_score += 0.3
            attention_reason = "Low mood or high stress detected"

    # Sleep check
    if metrics.sleep_hours:
        if metrics.sleep_hours < 6:
            risk_score += 0.2
            attention_reason = "Insufficient sleep detected"

    # Medication adherence check
    if metrics.medication_taken is False:
        risk_score += 0.2
        attention_reason = "Medication not taken"

    return min(risk_score, 1.0), attention_reason

async def process_health_checkin(
    db: AsyncSession,
    checkin_data: HealthCheckInCreate
) -> HealthCheckIn:
    """
    Process a health check-in, calculate risk score, and create notifications if needed.
    """
    # Get recent check-in history for trend analysis
    recent_checkins = await get_user_checkin_history(db, checkin_data.user_id, days=7)
    recent_checkins_data = [checkin.__dict__ for checkin in recent_checkins]
    
    # Add current check-in to history for analysis
    current_checkin = {
        'health_metrics': checkin_data.health_metrics.dict(),
        'check_in_time': checkin_data.check_in_time
    }
    recent_checkins_data.append(current_checkin)
    
    # Analyze health trends
    trend_analysis = predictive_analytics.analyze_health_trends(recent_checkins_data)
    
    # Calculate immediate risk score
    risk_score, attention_reason = await calculate_risk_score(checkin_data.health_metrics)
    
    # Adjust risk score based on trend analysis
    if trend_analysis['risk_level'] == 'high':
        risk_score = max(risk_score, 0.7)
        if not attention_reason:
            attention_reason = "Trend analysis indicates potential health concerns"
    
    # Create check-in record
    checkin = HealthCheckIn(
        user_id=checkin_data.user_id,
        check_in_time=checkin_data.check_in_time,
        health_metrics=checkin_data.health_metrics.dict(),
        risk_score=risk_score,
        requires_attention=risk_score >= 0.5,
        attention_reason=attention_reason
    )

    db.add(checkin)
    await db.commit()
    await db.refresh(checkin)

    # Send notification if attention is required
    if checkin.requires_attention:
        notification_message = f"Attention required: {attention_reason}"
        if trend_analysis['recommendations']:
            notification_message += f"\nRecommendations: {', '.join(trend_analysis['recommendations'])}"
            
        await send_notification(
            user_id=checkin_data.user_id,
            title="Health Check-in Alert",
            message=notification_message,
            notification_type="health_alert"
        )
        checkin.notification_sent = True
        checkin.notification_time = datetime.utcnow()
        await db.commit()

    return checkin

async def get_pending_checkins(db: AsyncSession) -> List[HealthCheckInSchedule]:
    """
    Get all scheduled check-ins that are due.
    """
    now = datetime.utcnow()
    result = await db.execute(
        select(HealthCheckInSchedule)
        .where(
            HealthCheckInSchedule.is_active == True,
            HealthCheckInSchedule.next_check_in <= now
        )
    )
    return result.scalars().all()

async def update_checkin_schedule(
    db: AsyncSession,
    schedule_id: int,
    last_check_in: datetime
) -> HealthCheckInSchedule:
    """
    Update the check-in schedule after a successful check-in.
    """
    schedule = await db.get(HealthCheckInSchedule, schedule_id)
    if not schedule:
        raise ValueError("Schedule not found")

    schedule.last_check_in = last_check_in
    
    # Calculate next check-in based on frequency
    if schedule.frequency == "daily":
        schedule.next_check_in = last_check_in + timedelta(days=1)
    elif schedule.frequency == "weekly":
        schedule.next_check_in = last_check_in + timedelta(weeks=1)
    elif schedule.frequency == "biweekly":
        schedule.next_check_in = last_check_in + timedelta(weeks=2)
    elif schedule.frequency == "monthly":
        schedule.next_check_in = last_check_in + timedelta(days=30)

    await db.commit()
    await db.refresh(schedule)
    return schedule

async def get_user_checkin_history(
    db: AsyncSession,
    user_id: int,
    days: int = 7
) -> List[HealthCheckIn]:
    """
    Get user's check-in history for the specified number of days.
    """
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(HealthCheckIn)
        .where(
            HealthCheckIn.user_id == user_id,
            HealthCheckIn.check_in_time >= since
        )
        .order_by(HealthCheckIn.check_in_time.desc())
    )
    return result.scalars().all() 