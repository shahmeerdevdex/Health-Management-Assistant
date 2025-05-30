from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from sqlalchemy.future import select
from app.api.endpoints.dependencies import get_db, get_current_user
from app.schemas.health_checkin import (
    HealthCheckInCreate,
    HealthCheckInResponse,
    CheckInScheduleCreate,
    CheckInScheduleResponse
)
from app.services.health_checkin_service import (
    process_health_checkin,
    get_pending_checkins,
    update_checkin_schedule,
    get_user_checkin_history
)
from app.db.models.user import User
from app.services.ai_services import PredictiveHealthAnalytics
from app.db.models.health_checkin import HealthCheckInSchedule
from datetime import timedelta, datetime
router = APIRouter()

@router.post("/check-in", response_model=HealthCheckInResponse)
async def create_health_checkin(
    checkin_data: HealthCheckInCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new health check-in entry.
    """
    if checkin_data.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to create check-in for another user")
    
    try:
        checkin = await process_health_checkin(db, checkin_data)
        return checkin
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[HealthCheckInResponse])
async def get_checkin_history(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's health check-in history.
    """
    try:
        history = await get_user_checkin_history(db, current_user.id, days)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def calculate_next_check_in(frequency: str, preferred_time: str) -> datetime:
    """Calculate the next check-in datetime based on frequency and preferred time."""
    now = datetime.utcnow()
    hour, minute = map(int, preferred_time.split(":"))
    base_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if base_time <= now:
        # Ensure next time is in the future
        base_time += timedelta(days=1)

    if frequency == "daily":
        return base_time
    elif frequency == "weekly":
        return base_time + timedelta(weeks=1)
    elif frequency == "biweekly":
        return base_time + timedelta(weeks=2)
    elif frequency == "monthly":
        return base_time + timedelta(days=30)
    return base_time

@router.post("/schedule", response_model=CheckInScheduleResponse)
async def create_checkin_schedule(
    schedule_data: CheckInScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new health check-in schedule."""
    if schedule_data.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to create schedule for another user")

    try:
        next_check = (
            calculate_next_check_in(schedule_data.frequency, schedule_data.preferred_time)
            if schedule_data.preferred_time else None
        )

        schedule = HealthCheckInSchedule(
            user_id=schedule_data.user_id,
            frequency=schedule_data.frequency,
            preferred_time=schedule_data.preferred_time,
            reminder_preferences=schedule_data.reminder_preferences.dict(),
            next_check_in=next_check
        )

        db.add(schedule)
        await db.commit()
        await db.refresh(schedule)
        return schedule

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule", response_model=CheckInScheduleResponse)
async def get_checkin_schedule(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's current health check-in schedule.
    """
    try:
        result = await db.execute(
            select(HealthCheckInSchedule).where(
                HealthCheckInSchedule.user_id == current_user.id,
                HealthCheckInSchedule.is_active == True
            )
        )
        schedule = result.scalars().first()
        if not schedule:
            raise HTTPException(status_code=404, detail="No active schedule found")
        return schedule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/schedule/{schedule_id}", response_model=CheckInScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: CheckInScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing health check-in schedule.
    """
    if schedule_data.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update schedule for another user")
    
    try:
        schedule = await db.get(HealthCheckInSchedule, schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        for key, value in schedule_data.dict().items():
            setattr(schedule, key, value)
        
        await db.commit()
        await db.refresh(schedule)
        return schedule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictive-insights", response_model=dict)
async def get_predictive_insights(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get predictive health insights based on recent check-in history.
    """
    try:
        # Get recent check-in history
        history = await get_user_checkin_history(db, current_user.id, days)
        history_data = [checkin.__dict__ for checkin in history]

        # Instantiate and call the analysis
        analyzer = PredictiveHealthAnalytics()
        insights = analyzer.analyze_health_trends(history_data)

        return {
            "user_id": current_user.id,
            "analysis_period_days": days,
            "risk_level": insights["risk_level"],
            "health_trends": insights["trends"],
            "recommendations": insights["recommendations"],
            "last_check_in": history[0].check_in_time if history else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
