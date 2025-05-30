# schemas/therapy.py
from pydantic import BaseModel
from typing import List, Optional

class TherapyGuidanceRequest(BaseModel):
    condition: str
    symptoms: List[str]
    age: Optional[int] = None
    medical_history: Optional[List[str]] = None

class TherapyGuidanceResponse(BaseModel):
    recommended_therapies: List[str]
    description: Optional[str] = None

# services/therapy_service.py
from sqlalchemy.orm import Session
from app.schemas.therapy import TherapyGuidanceRequest, TherapyGuidanceResponse

async def get_therapy_guidance(request: TherapyGuidanceRequest, db: Session) -> TherapyGuidanceResponse:
    """
    Processes the request to provide therapy recommendations.
    """
    # Mocked therapy recommendation logic
    therapy_map = {
        "anxiety": ["Cognitive Behavioral Therapy (CBT)", "Mindfulness Meditation"],
        "back_pain": ["Physical Therapy", "Posture Correction Exercises"],
        "depression": ["CBT", "Light Therapy", "Guided Journaling"],
    }
    
    recommended_therapies = therapy_map.get(request.condition.lower(), ["General Stress Management Techniques"])
    description = f"Recommended therapies for {request.condition}: {', '.join(recommended_therapies)}"
    
    return TherapyGuidanceResponse(
        recommended_therapies=recommended_therapies,
        description=description
    )
