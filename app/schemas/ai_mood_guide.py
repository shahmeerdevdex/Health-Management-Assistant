from pydantic import BaseModel
from typing import List, Dict, Optional

class MentalHealthRequest(BaseModel):
    user_id: int
    mood_logs: Optional[List[str]] = None  # ["stressed", "happy", "anxious"]
    health_data: Optional[Dict[str, float]] = None  # {"sleep_hours": 6, "hydration_level": 40}
    social_interactions: Optional[List[str]] = None  # ["Talked to a friend", "Avoided group meetings"]
    goals_progress: Optional[Dict[str, float]] = None  # {"exercise": 70, "meditation": 50}
    mood_board: Optional[Dict[str, str]] = None  # {"image_url": "https://img.com/happy.jpg", "music": "calm.mp3"}
    preferences: Optional[List[str]] = None  # ["mindfulness", "predictive insights"]

class AIInsight(BaseModel):
    category: str
    insight: str

class MentalHealthResponse(BaseModel):
    user_id: int
    insights: List[AIInsight]
    recommendations: List[str]

class CarePlanResponse(BaseModel):
    date: str
    goals: List[str]
