from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.gamification import (
    GamificationRequest,
    GamificationResponse,
    LeaderboardResponse
)
from app.services.gamification_service import (
    process_gamification_rewards,
    get_leaderboard
)
from app.api.endpoints.dependencies import get_db, get_current_user

router = APIRouter()

@router.post("/rewards", response_model=GamificationResponse)
async def gamification_rewards(
    request: GamificationRequest,
    db: AsyncSession = Depends(get_db),
    db_user=Depends(get_current_user)
):
    """
    Processes user progress and rewards them based on health goals and activities.
    Users earn points for logging symptoms, completing health tasks, and adhering to medication schedules.
    """
    if not db_user:
        raise HTTPException(status_code=401, detail="User authentication required.")

    try:
        rewards_data = await process_gamification_rewards(request, db)
        return rewards_data
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing rewards.")

@router.get("/leaderboard", response_model=list[LeaderboardResponse])
async def gamification_leaderboard(
    db: AsyncSession = Depends(get_db),
    db_user=Depends(get_current_user)
):
    """
    Retrieves the leaderboard ranking users based on health engagement metrics.
    Users are ranked based on challenge completion, symptom logging, and medication adherence.
    """
    if not db_user:
        raise HTTPException(status_code=401, detail="Authentication required.")

    try:
        leaderboard = await get_leaderboard(db)
        return leaderboard
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch leaderboard.")
