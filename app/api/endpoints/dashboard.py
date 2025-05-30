from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.endpoints.dependencies import get_current_user, get_db
from app.services.dashboard import build_user_dashboard
from app.services.ai_services import detect_health_patterns

router = APIRouter()

@router.get("/")
async def get_dashboard_endpoint(
    db: AsyncSession = Depends(get_db),
    db_user=Depends(get_current_user)
):
    """
    Professional user dashboard:
    - Latest mood entry
    - Pending medications
    - Upcoming appointments
    - Notifications
    - Subscription
    - AI Insights
    """
    dashboard_data = await build_user_dashboard(db, db_user.id)
    return dashboard_data


@router.post("/ai-insights")
async def get_ai_insights_endpoint(
    db_user=Depends(get_current_user)
):
    return await detect_health_patterns(db_user.id)
