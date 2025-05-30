from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class MentalHealthRequest(BaseModel):
    """User input for mental health insights generation."""
    
    user_id: int = Field(..., description="Unique identifier for the user")
    
    mood_logs: Optional[List[str]] = Field(
        default=None,
        description="List of mood entries (e.g., ['happy', 'anxious'])"
    )
    
    health_data: Optional[Dict[str, float]] = Field(
        default=None,
        description="Health metrics like sleep_hours, hydration_level, etc."
    )
    
    social_interactions: Optional[List[str]] = Field(
        default=None,
        description="Notable social interactions or events"
    )
    
    goals_progress: Optional[Dict[str, float]] = Field(
        default=None,
        description="Progress toward personal goals (e.g., {'exercise': 75})"
    )
    
    mood_board: Optional[Dict[str, str]] = Field(
        default=None,
        description="Mood board inputs such as image_url, music, or quotes"
    )
    
    preferences: Optional[List[str]] = Field(
        default=None,
        description="User preferences like 'mindfulness', 'predictive insights'"
    )


class AIInsight(BaseModel):
    """A single AI-generated insight."""
    
    category: str = Field(..., description="Insight category (e.g., 'Mood Trend')")
    insight: str = Field(..., description="Text of the insight")


class MentalHealthResponse(BaseModel):
    """Response containing AI-generated insights and recommendations."""
    
    user_id: int
    insights: List[AIInsight]
    recommendations: List[str]


class MoodAvatar(BaseModel):
    """Represents a summary avatar based on mood data."""
    
    text: str = Field(..., description="Label for mood avatar")
    color: str = Field(..., description="Associated color for visualization")
    description: str = Field(..., description="Explanation of the avatar")


class TimeOfDayTrend(BaseModel):
    """Mood patterns based on time of day."""
    
    dominant_mood: str
    mood_distribution: Dict[str, int]
    average_mood: float


class HourlyPattern(BaseModel):
    """Mood statistics for a specific hour."""
    
    average: float
    count: int


class MoodPatternResponse(BaseModel):
    """Aggregated mood patterns for a user."""
    
    user_id: int
    mood_avatar: MoodAvatar
    time_of_day_trend: Dict[str, TimeOfDayTrend]
    hourly_patterns: Dict[int, HourlyPattern]
    most_common_mood: str


class SelfCompassionResponse(BaseModel):
    """Scores and suggestions based on self-compassion analysis."""
    
    user_id: int
    score: int = Field(..., ge=0, le=100, description="Self-compassion score (0-100)")
    factors: List[str]
    suggestions: List[str]


class MoodStabilityResponse(BaseModel):
    """Tracks mood consistency and volatility trends."""
    
    user_id: int
    stability_score: int = Field(..., ge=0, le=100)
    volatility: float
    trend: str = Field(..., description="'improving', 'declining', 'stable', or 'neutral'")
    average_mood: float


class CarePlanResponse(BaseModel):
    """Recommended care plan with actionable goals."""
    
    date: str = Field(..., description="Date of the care plan (ISO format)")
    goals: List[str] = Field(..., description="List of suggested goals")
