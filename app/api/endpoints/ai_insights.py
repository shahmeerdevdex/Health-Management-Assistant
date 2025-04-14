from fastapi import APIRouter, Depends, HTTPException
from app.services.ai_services import (
    analyze_symptoms,
    get_personalized_health_tips,
    detect_health_patterns,
    analyze_symptom_checker,
    generate_health_education,
    generate_personalized_plan
)
from app.api.endpoints.dependencies import get_current_user
from pydantic import BaseModel
from typing import List
from app.schemas.ai_mood_guide import CarePlanResponse
from app.api.endpoints.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.health_diary import get_mood_entries_with_time
from app.services.ai_mood_guide import analyze_mood_patterns
from app.crud.health_diary import get_mood_counts, get_last_diary_entry_date
from app.services.ai_services import assess_mental_health_risk


router = APIRouter()

class SymptomCheckerRequest(BaseModel):
    symptoms: List[str]

class HealthEducationRequest(BaseModel):
    topics: List[str]  # List of health topics the user is interested in

@router.post("/analyze-symptoms")
async def analyze_symptoms_endpoint(
    db_user=Depends(get_current_user)
):
    """Analyze user symptoms and provide AI-driven insights. Requires authentication."""
    return await analyze_symptoms(db_user.id)

@router.get("/health-tips")
async def get_health_tips_endpoint(
    db_user=Depends(get_current_user)
):
    """Fetch personalized health tips based on the user's health data. Requires authentication."""
    return await get_personalized_health_tips(db_user.id)

@router.post("/pattern-recognition")
async def detect_health_patterns_endpoint(
    db_user=Depends(get_current_user)
):
    """Detect health patterns based on the user's symptom history. Requires authentication."""
    return await detect_health_patterns(db_user.id)

@router.post("/symptom-checker")
async def symptom_checker_endpoint(
    request: SymptomCheckerRequest,
    db_user=Depends(get_current_user)
):
    """
    AI-powered symptom checker that analyzes symptoms and provides:
    - Possible conditions
    - Urgency level (Low, Moderate, High, Emergency)
    - Recommended next steps
    """
    result = await analyze_symptom_checker(db_user.id, request.symptoms)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return {
        "conditions": result["conditions"],
        "urgency_level": result["urgency_level"],
        "next_steps": result["next_steps"]
    }

@router.post("/health-education")
async def health_education_endpoint(
    request: HealthEducationRequest,
    db_user=Depends(get_current_user)
):
    """Provides AI-powered personalized health education based on user-selected topics."""
    return await generate_health_education(db_user.id, request.topics)

@router.get("/care-plan/{user_id}", response_model=CarePlanResponse)
async def get_care_plan(user_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    plan = await generate_personalized_plan(db, user_id)
    return plan

@router.get("/mood-analytics/{user_id}")
async def mood_analytics(user_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    entries = await get_mood_entries_with_time(db, user_id)
    result = await analyze_mood_patterns(entries)
    return result

@router.get("/predictive-alerts/{user_id}")
async def predictive_alert(user_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    mood_counts = await get_mood_counts(db, user_id)
    last_entry = await get_last_diary_entry_date(db, user_id)
    result = assess_mental_health_risk(mood_counts, last_entry)
    return result