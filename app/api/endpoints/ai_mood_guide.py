from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.endpoints.dependencies import get_db, get_current_user
from app.schemas.ai_mood_guide import MentalHealthRequest, MentalHealthResponse, AIInsight
from app.services.ai_mood_guide import analyze_mental_health

router = APIRouter()

@router.post("/ai/mental-health-insights", response_model=MentalHealthResponse)
async def get_mental_health_insights(
    user_input: MentalHealthRequest,
    db: Session = Depends(get_db),
    db_user=Depends(get_current_user)
):
    """Unified AI-powered endpoint for mental health insights."""
    result = await analyze_mental_health(user_input)

    if not isinstance(result, dict) or "insights" not in result or "recommendations" not in result:
        return {"detail": "Invalid AI response format"}

    return MentalHealthResponse(
        user_id=user_input.user_id,
        insights=[AIInsight(category=i["category"], insight=i["insight"]) for i in result["insights"]],
        recommendations=result["recommendations"]
    )
