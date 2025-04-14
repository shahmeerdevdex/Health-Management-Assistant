from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class GamificationRequest(BaseModel):
    user_id: int
    completed_goals: List[str] = []  # Ensure it defaults to an empty list if not provided
    total_steps: Optional[int] = 0  # Daily or weekly steps count
    medication_adherence: Optional[float] = 0.0  # Percentage of adherence
    workout_sessions: Optional[int] = 0  # Count of completed workout sessions

class GamificationResponse(BaseModel):
    user_id: int
    points: int
    badges: List[str]  # Convert from a string in the DB
    completed_challenges: int
    last_updated: datetime
    progress_message: str

    class Config:
        from_attributes = True  # If using FastAPI v2, change to orm_mode = True

class LeaderboardResponse(BaseModel):
    user_id: int
    total_points: int
    last_updated: datetime

    class Config:
        from_attributes = True  # Change to orm_mode = True for Pydantic v2
