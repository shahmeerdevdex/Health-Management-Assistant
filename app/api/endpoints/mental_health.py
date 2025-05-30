from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.endpoints.dependencies import get_current_user, get_db
from app.db.models.user import User
from app.schemas.mental_health import (
    ProfessionalCreate,
    ProfessionalUpdate,
    ProfessionalResponse,
    TherapistAppointmentCreate,
    TherapistAppointmentUpdate,
    TherapistAppointmentResponse,
    MentalHealthAssessmentCreate,
    MentalHealthAssessmentUpdate,
    MentalHealthAssessmentResponse,
    CrisisInterventionCreate,
    CrisisInterventionUpdate,
    CrisisInterventionResponse,
    MentalHealthResourceCreate,
    MentalHealthResourceUpdate,
    MentalHealthResourceResponse,
    TherapistReviewCreate,
    TherapistReviewUpdate,
    TherapistReviewResponse,
    MentalHealthHistoryResponse
)
from app.services.mental_health_service import (
    create_professional,
    get_professional,
    update_professional,
    get_professionals,
    create_therapist_appointment,
    update_appointment,
    create_mental_health_assessment,
    update_assessment,
    create_crisis_intervention,
    update_crisis_intervention,
    create_mental_health_resource,
    get_mental_health_resources,
    create_therapist_review,
    update_review,
    get_user_mental_health_history
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Professional Endpoints
@router.post("/professionals", response_model=ProfessionalResponse)
async def create_new_professional(
    professional_data: ProfessionalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new mental health professional profile."""
    try:
        professional = await create_professional(db, professional_data)
        return professional
    except Exception as e:
        logger.error(f"Error creating professional: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating professional profile")

@router.get("/professionals/{professional_id}", response_model=ProfessionalResponse)
async def get_professional_by_id(
    professional_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a professional by ID."""
    professional = await get_professional(db, professional_id)
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    return professional

@router.put("/professionals/{professional_id}", response_model=ProfessionalResponse)
async def update_professional_profile(
    professional_id: int,
    update_data: ProfessionalUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a professional's profile."""
    professional = await update_professional(db, professional_id, update_data)
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    return professional

@router.get("/professionals", response_model=List[ProfessionalResponse])
async def list_professionals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of all professionals."""
    professionals = await get_professionals(db)
    return professionals

# Appointment Endpoints
@router.post("/appointments", response_model=TherapistAppointmentResponse)
async def create_new_appointment(
    appointment_data: TherapistAppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new therapist appointment."""
    try:
        appointment = await create_therapist_appointment(db, appointment_data)
        return appointment
    except Exception as e:
        logger.error(f"Error creating appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating appointment")

@router.put("/appointments/{appointment_id}", response_model=TherapistAppointmentResponse)
async def update_appointment_details(
    appointment_id: int,
    update_data: TherapistAppointmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an appointment."""
    appointment = await update_appointment(db, appointment_id, update_data)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

# Assessment Endpoints
@router.post("/assessments", response_model=MentalHealthAssessmentResponse)
async def create_new_assessment(
    assessment_data: MentalHealthAssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new mental health assessment."""
    try:
        assessment = await create_mental_health_assessment(db, assessment_data)
        return assessment
    except Exception as e:
        logger.error(f"Error creating assessment: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating assessment")

@router.put("/assessments/{assessment_id}", response_model=MentalHealthAssessmentResponse)
async def update_assessment_details(
    assessment_id: int,
    update_data: MentalHealthAssessmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a mental health assessment."""
    assessment = await update_assessment(db, assessment_id, update_data)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment

# Crisis Intervention Endpoints
@router.post("/crisis", response_model=CrisisInterventionResponse)
async def create_new_crisis_intervention(
    crisis_data: CrisisInterventionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new crisis intervention record."""
    try:
        crisis = await create_crisis_intervention(db, crisis_data)
        return crisis
    except Exception as e:
        logger.error(f"Error creating crisis intervention: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating crisis intervention")

@router.put("/crisis/{crisis_id}", response_model=CrisisInterventionResponse)
async def update_crisis_intervention_details(
    crisis_id: int,
    update_data: CrisisInterventionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a crisis intervention record."""
    crisis = await update_crisis_intervention(db, crisis_id, update_data)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis intervention not found")
    return crisis

# Resource Endpoints
@router.post("/resources", response_model=MentalHealthResourceResponse)
async def create_new_resource(
    resource_data: MentalHealthResourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new mental health resource."""
    try:
        resource = await create_mental_health_resource(db, resource_data)
        return resource
    except Exception as e:
        logger.error(f"Error creating resource: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating resource")

@router.get("/resources", response_model=List[MentalHealthResourceResponse])
async def list_resources(
    db: AsyncSession = Depends(get_db)
):
    """Get all mental health resources."""
    try:
        resources = await get_mental_health_resources(db)
        return resources
    except Exception as e:
        logger.error(f"Error getting resources: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving resources")

# Review Endpoints
@router.post("/reviews", response_model=TherapistReviewResponse)
async def create_new_review(
    review_data: TherapistReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new therapist review."""
    try:
        review = await create_therapist_review(db, review_data)
        return review
    except Exception as e:
        logger.error(f"Error creating review: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating review")

@router.put("/reviews/{review_id}", response_model=TherapistReviewResponse)
async def update_review_details(
    review_id: int,
    update_data: TherapistReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a therapist review."""
    review = await update_review(db, review_id, update_data)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review

# History Endpoint
@router.get("/history", response_model=MentalHealthHistoryResponse)
async def get_mental_health_history(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's mental health history."""
    try:
        history = await get_user_mental_health_history(db, current_user.id, days)
        return history
    except Exception as e:
        logger.error(f"Error getting mental health history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving mental health history") 