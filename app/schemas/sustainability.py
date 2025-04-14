from pydantic import BaseModel
from typing import List, Optional

class SustainabilityRequest(BaseModel):
    user_id: int  # The user submitting sustainability data or request
    health_practices: List[str]  # List of sustainable health practices followed
    medication_waste_reduction: Optional[bool] = False  # Whether the user follows waste reduction in medication usage
    telehealth_usage: Optional[bool] = False  # Whether the user prefers telehealth over in-person visits

class SustainabilityInsight(BaseModel):
    insight: str  # AI-generated or predefined insight on sustainability

class SustainabilityResponse(BaseModel):
    user_id: int
    insights: List[SustainabilityInsight]  # Insights and recommendations based on user inputs
    recommendation: str  # Suggested next steps to improve sustainable health practices
