from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.therapy import TherapyGuidanceRequest, TherapyGuidanceResponse
from app.services.therapy_services import get_therapy_guidance
from app.api.endpoints.dependencies import get_db, get_current_user

router = APIRouter()

@router.post("/guidance", response_model=TherapyGuidanceResponse)
async def therapy_guidance(
    request: TherapyGuidanceRequest,
    db: AsyncSession = Depends(get_db),
    db_user=Depends(get_current_user)
):
    """
    AI-powered non-invasive therapy guidance.

    This endpoint uses AI to suggest personalized, evidence-based therapy options 
    for the user's specified condition. Suggestions may include:

    - Cognitive Behavioral Therapy (CBT)
    - Mindfulness or Meditation
    - Breathing and Relaxation Techniques
    - Physical or Occupational Therapy
    - Sleep or Stress Management Interventions

    Requires authentication.
    """
    try:
        return await get_therapy_guidance(request, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Therapy guidance failed: {str(e)}")
