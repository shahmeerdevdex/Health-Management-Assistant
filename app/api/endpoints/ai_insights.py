from fastapi import APIRouter, Depends, HTTPException
from app.core.ai_services import analyze_symptoms, get_personalized_health_tips, detect_health_patterns
from app.services.auth_service import verify_access_token  # Import authentication function

router = APIRouter()

async def get_current_user(token: str = Depends(verify_access_token)):
    """Dependency to validate and return the current authenticated user from the token."""
    return token  # Returns the user's data if the token is valid


@router.post("/ai/analyze-symptoms", dependencies=[Depends(get_current_user)])
async def analyze_symptoms_endpoint(user_id: int):
    """Analyze user symptoms and provide AI-driven insights. Requires authentication."""
    return await analyze_symptoms(user_id)


@router.get("/ai/health-tips/{user_id}", dependencies=[Depends(get_current_user)])
async def get_health_tips_endpoint(user_id: int):
    """Fetch personalized health tips based on the user's health data. Requires authentication."""
    return await get_personalized_health_tips(user_id)


@router.post("/ai/pattern-recognition", dependencies=[Depends(get_current_user)])
async def detect_health_patterns_endpoint(user_id: int):
    """Detect health patterns based on the user's symptom history. Requires authentication."""
    return await detect_health_patterns(user_id)
