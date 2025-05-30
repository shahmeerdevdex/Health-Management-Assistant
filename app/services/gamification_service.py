from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.gamification import GamificationRequest, GamificationResponse, LeaderboardResponse
from app.db.models.gamification import Gamification, Leaderboard
from datetime import datetime
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

async def process_gamification_rewards(request: GamificationRequest, db: AsyncSession) -> GamificationResponse:
    """
    Processes user progress and updates gamification rewards.
    """
    rewards = []
    points_earned = 0

    # Fetch or create user gamification record
    gamification_query = await db.execute(select(Gamification).filter(Gamification.user_id == request.user_id))
    gamification_entry = gamification_query.scalar_one_or_none()

    if not gamification_entry:
        gamification_entry = Gamification(user_id=request.user_id, points=0, completed_challenges=0, badges="", last_updated=datetime.utcnow())
        db.add(gamification_entry)

    # Reward system
    if request.completed_goals:
        points_earned += len(request.completed_goals) * 10
        rewards.append(f"Completed {len(request.completed_goals)} health goals! Earned a wellness badge.")

    if request.total_steps >= 10000:
        points_earned += 50
        rewards.append("You've reached 10,000 steps! Reward: Fitness Boost Badge.")
    elif request.total_steps >= 5000:
        points_earned += 25
        rewards.append("You've reached 5,000 steps! Keep going!")

    if request.medication_adherence >= 90:
        points_earned += 30
        rewards.append("Excellent medication adherence! Reward: Health Consistency Award.")
    elif request.medication_adherence >= 75:
        points_earned += 15
        rewards.append("Good adherence! Keep it up!")

    if request.workout_sessions >= 5:
        points_earned += 40
        rewards.append("Great job on completing 5 workouts! Reward: Active Lifestyle Badge.")

    # Update user gamification data
    gamification_entry.points += points_earned
    gamification_entry.completed_challenges += len(request.completed_goals)
    gamification_entry.badges = ", ".join(rewards) if rewards else gamification_entry.badges
    gamification_entry.last_updated = datetime.utcnow()

    db.add(gamification_entry)

    # Update leaderboard
    leaderboard_query = await db.execute(select(Leaderboard).filter(Leaderboard.user_id == request.user_id))
    leaderboard_entry = leaderboard_query.scalar_one_or_none()

    if not leaderboard_entry:
        leaderboard_entry = Leaderboard(user_id=request.user_id, total_points=points_earned, last_updated=datetime.utcnow())
        db.add(leaderboard_entry)
    else:
        leaderboard_entry.total_points += points_earned
        leaderboard_entry.last_updated = datetime.utcnow()

    db.add(leaderboard_entry)

    # Commit transaction
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Database commit failed: {e}", exc_info=True)
        raise

    # Fix: Refresh before accessing attributes
    await db.refresh(gamification_entry)

    return GamificationResponse(
        user_id=request.user_id,
        points=gamification_entry.points,
        badges=gamification_entry.badges.split(", ") if gamification_entry.badges else [],  # ✅ Fixed badges field conversion
        completed_challenges=gamification_entry.completed_challenges,
        last_updated=gamification_entry.last_updated,
        progress_message="Keep up the great work on your health journey!"
    )
async def get_leaderboard(db: AsyncSession) -> list[LeaderboardResponse]:
    """
    Retrieves the leaderboard sorted by total points.
    """
    leaderboard_query = await db.execute(select(Leaderboard).order_by(Leaderboard.total_points.desc()))
    leaderboard_entries = leaderboard_query.scalars().all()

    return [
        LeaderboardResponse(
            user_id=entry.user_id,
            total_points=entry.total_points,
            last_updated=entry.last_updated
        ) for entry in leaderboard_entries
    ]
