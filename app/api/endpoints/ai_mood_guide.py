from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.api.endpoints.dependencies import get_db, get_current_user
from app.schemas.ai_mood_guide import (
    MentalHealthRequest,
    MentalHealthResponse,
    AIInsight,
    MoodPatternResponse,
    SelfCompassionResponse,
    MoodStabilityResponse
)
from app.services.ai_mood_guide import (
    analyze_mental_health,
    analyze_mood_patterns,
    calculate_self_compassion_score,
    calculate_mood_stability
)
from app.crud.health_diary import get_mood_entries_with_time

router = APIRouter()

@router.post("/ai/mental-health-insights", response_model=MentalHealthResponse)
async def get_mental_health_insights(
    user_input: MentalHealthRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Unified AI-powered endpoint for mental health insights."""
    try:
        # Validate user authorization
        if user_input.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to access this user's data")

        result = await analyze_mental_health(user_input)

        if not isinstance(result, dict) or "insights" not in result or "recommendations" not in result:
            raise HTTPException(status_code=500, detail="Invalid AI response format")

        return MentalHealthResponse(
            user_id=user_input.user_id,
            insights=[AIInsight(category=i["category"], insight=i["insight"]) for i in result["insights"]],
            recommendations=result["recommendations"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai/mood-patterns/{user_id}", response_model=MoodPatternResponse)
async def get_mood_patterns(
    user_id: int,
    days: Optional[int] = 30,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get detailed mood patterns and analytics."""
    try:
        # Validate user authorization
        if user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to access this user's data")

        # Validate days parameter
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 365")

        # Get mood entries
        entries = await get_mood_entries_with_time(db, user_id)
        if not entries:
            raise HTTPException(status_code=404, detail="No mood entries found")

        # Analyze patterns
        patterns = await analyze_mood_patterns(entries)
        return MoodPatternResponse(
            user_id=user_id,
            mood_avatar=patterns["mood_avatar"],
            time_of_day_trend=patterns["time_of_day_trend"],
            hourly_patterns=patterns["hourly_patterns"],
            most_common_mood=patterns["most_common_mood"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai/self-compassion/{user_id}", response_model=SelfCompassionResponse)
async def get_self_compassion_score(
    user_id: int,
    days: Optional[int] = 30,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get self-compassion score and analysis."""
    try:
        # Validate user authorization
        if user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to access this user's data")

        # Get mood entries
        entries = await get_mood_entries_with_time(db, user_id)
        if not entries:
            raise HTTPException(status_code=404, detail="No mood entries found")

        # Get time trends for context
        patterns = await analyze_mood_patterns(entries)
        
        # Calculate self-compassion score
        score_data = calculate_self_compassion_score(entries, patterns["time_of_day_trend"])
        
        return SelfCompassionResponse(
            user_id=user_id,
            score=score_data["score"],
            factors=score_data["factors"],
            suggestions=score_data["suggestions"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai/mood-stability/{user_id}", response_model=MoodStabilityResponse)
async def get_mood_stability(
    user_id: int,
    days: Optional[int] = 30,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get mood stability metrics and analysis."""
    try:
        # Validate user authorization
        if user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to access this user's data")

        # Get mood entries
        entries = await get_mood_entries_with_time(db, user_id)
        if not entries:
            raise HTTPException(status_code=404, detail="No mood entries found")

        # Calculate stability metrics
        stability_data = calculate_mood_stability(entries)
        
        return MoodStabilityResponse(
            user_id=user_id,
            stability_score=stability_data["stability_score"],
            volatility=stability_data["volatility"],
            trend=stability_data["trend"],
            average_mood=stability_data["average_mood"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
