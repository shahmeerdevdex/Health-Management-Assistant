from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from app.db.models.mental_health import Professional
from app.db.models.mental_health import (
    Professional,
    TherapistAppointment,
    MentalHealthAssessment,
    CrisisIntervention,
    MentalHealthResource,
    TherapistReview,
    TherapyType,
    TherapyApproach
)
from app.schemas.mental_health import (
    ProfessionalCreate,
    ProfessionalUpdate,
    TherapistAppointmentCreate,
    TherapistAppointmentUpdate,
    MentalHealthAssessmentCreate,
    MentalHealthAssessmentUpdate,
    CrisisInterventionCreate,
    CrisisInterventionUpdate,
    MentalHealthResourceCreate,
    MentalHealthResourceUpdate,
    TherapistReviewCreate,
    TherapistReviewUpdate
)
from app.services.notification_service import send_notification
import logging
from app.schemas.user import UserCreate
from app.crud.user import create_user

logger = logging.getLogger(__name__)

# Professional Management
async def create_professional(db: AsyncSession, professional_data: ProfessionalCreate) -> Professional:
    """Create a new mental health professional profile."""
    # Create a new user for the professional
    user_data = UserCreate(
        email=professional_data.email,  # Use the email field
        full_name=professional_data.name,
        password="changeme123",  # Default password that should be changed
        role="PROFESSIONAL"
    )
    
    # Create the user first
    user = await create_user(db, user_data)
    
    # Create professional data with the new user_id
    professional_dict = professional_data.dict()
    professional_dict['user_id'] = user.id
    professional_dict.pop('email', None)  # Remove email field as it's not in the Professional model
    
    # Create the professional profile
    professional = Professional(**professional_dict)
    db.add(professional)
    await db.commit()
    await db.refresh(professional)
    
    # Add email to the professional object for response
    professional.email = user.email
    
    return professional

async def get_professional(db: AsyncSession, professional_id: int) -> Optional[Professional]:
    """Get a professional by ID."""
    query = select(Professional).options(selectinload(Professional.user)).where(Professional.id == professional_id)
    result = await db.execute(query)
    professional = result.scalar_one_or_none()
    
    if professional:
        professional.email = professional.user.email
    
    return professional

async def update_professional(
    db: AsyncSession,
    professional_id: int,
    update_data: ProfessionalUpdate
) -> Optional[Professional]:
    """Update a professional's profile."""
    professional = await get_professional(db, professional_id)
    if not professional:
        return None
    
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(professional, field, value)
    
    await db.commit()
    await db.refresh(professional)
    return professional


async def get_professionals(
    db: AsyncSession
) -> List[Professional]:
    """Get list of all professionals with user email preloaded."""
    query = select(Professional).options(selectinload(Professional.user))
    result = await db.execute(query)
    professionals = result.scalars().all()

    # Safely access preloaded related data
    for professional in professionals:
        professional.email = professional.user.email

    return professionals

# Appointment Management
async def create_therapist_appointment(
    db: AsyncSession,
    appointment_data: TherapistAppointmentCreate
) -> TherapistAppointment:
    """Create a new therapist appointment."""
    # Convert timezone-aware datetimes to timezone-naive
    appointment_dict = appointment_data.dict()
    if appointment_dict['date_time'].tzinfo is not None:
        appointment_dict['date_time'] = appointment_dict['date_time'].replace(tzinfo=None)
    if appointment_dict.get('follow_up_date') and appointment_dict['follow_up_date'].tzinfo is not None:
        appointment_dict['follow_up_date'] = appointment_dict['follow_up_date'].replace(tzinfo=None)
    
    # Convert enum values to uppercase for database compatibility
    appointment_dict['session_type'] = appointment_dict['session_type'].value.upper()
    
    # Map therapy approach values to database enum values
    approach_mapping = {
        'cognitive_behavioral': 'CBT',
        'dialectical_behavioral': 'DBT',
        'psychodynamic': 'PSYCHODYNAMIC',
        'humanistic': 'HUMANISTIC',
        'mindfulness': 'MINDFULNESS',
        'other': 'OTHER'
    }
    if appointment_dict.get('approach'):
        approach_value = appointment_dict['approach'].value.lower()
        appointment_dict['approach'] = approach_mapping.get(approach_value, 'OTHER')
    
    appointment = TherapistAppointment(**appointment_dict)
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)
    
    # Load the therapist relationship
    query = select(Professional).where(Professional.id == appointment.therapist_id)
    result = await db.execute(query)
    therapist = result.scalar_one()
    
    # Send notification to both user and therapist
    await send_notification(
        user_id=appointment.user_id,
        title="New Therapy Appointment",
        message=f"Your appointment with {therapist.name} is scheduled for {appointment.date_time}",
        notification_type="appointment"
    )
    
    await send_notification(
        user_id=therapist.user_id,
        title="New Appointment",
        message=f"New appointment scheduled with user ID {appointment.user_id} for {appointment.date_time}",
        notification_type="appointment"
    )
    
    return appointment

async def update_appointment(
    db: AsyncSession,
    appointment_id: int,
    update_data: TherapistAppointmentUpdate
) -> Optional[TherapistAppointment]:
    """Update an appointment."""
    result = await db.execute(select(TherapistAppointment).where(TherapistAppointment.id == appointment_id))
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        return None
    
    # Convert update data to dict and handle timezone-aware datetimes
    update_dict = update_data.dict(exclude_unset=True)
    if 'follow_up_date' in update_dict and update_dict['follow_up_date'] and update_dict['follow_up_date'].tzinfo is not None:
        update_dict['follow_up_date'] = update_dict['follow_up_date'].replace(tzinfo=None)
    
    # Update appointment fields
    for field, value in update_dict.items():
        setattr(appointment, field, value)
    
    await db.commit()
    await db.refresh(appointment)
    return appointment

# Assessment Management
async def create_mental_health_assessment(
    db: AsyncSession,
    assessment_data: MentalHealthAssessmentCreate
) -> MentalHealthAssessment:
    """Create a new mental health assessment."""
    assessment_dict = assessment_data.dict()
    
    # Handle timezone-aware datetimes
    if assessment_dict.get('follow_up_date') and assessment_dict['follow_up_date'].tzinfo is not None:
        assessment_dict['follow_up_date'] = assessment_dict['follow_up_date'].replace(tzinfo=None)
    
    assessment = MentalHealthAssessment(**assessment_dict)
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)
    
    # Send notification if high risk
    if assessment.risk_level == "High":
        await send_notification(
            user_id=assessment.user_id,
            title="High Risk Assessment",
            message="Your recent mental health assessment indicates high risk. Please seek professional help.",
            notification_type="assessment"
        )
    
    return assessment

async def update_assessment(
    db: AsyncSession,
    assessment_id: int,
    update_data: MentalHealthAssessmentUpdate
) -> Optional[MentalHealthAssessment]:
    """Update a mental health assessment."""
    result = await db.execute(select(MentalHealthAssessment).where(MentalHealthAssessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    
    if not assessment:
        return None
    
    # Convert update data to dict and handle timezone-aware datetimes
    update_dict = update_data.dict(exclude_unset=True)
    if 'follow_up_date' in update_dict and update_dict['follow_up_date'] and update_dict['follow_up_date'].tzinfo is not None:
        update_dict['follow_up_date'] = update_dict['follow_up_date'].replace(tzinfo=None)
    
    for field, value in update_dict.items():
        setattr(assessment, field, value)
    
    await db.commit()
    await db.refresh(assessment)
    return assessment

# Crisis Intervention
async def create_crisis_intervention(
    db: AsyncSession,
    crisis_data: CrisisInterventionCreate
) -> CrisisIntervention:
    """Create a new crisis intervention record."""
    crisis_dict = crisis_data.dict()
    
    # Handle timezone-aware datetimes
    if crisis_dict.get('follow_up_date') and crisis_dict['follow_up_date'].tzinfo is not None:
        crisis_dict['follow_up_date'] = crisis_dict['follow_up_date'].replace(tzinfo=None)
    
    # Handle responder_id - set to None if it's 0 or not a valid professional
    if crisis_dict.get('responder_id') == 0:
        crisis_dict['responder_id'] = None
    elif crisis_dict.get('responder_id'):
        # Verify that the responder exists
        result = await db.execute(
            select(Professional).where(Professional.id == crisis_dict['responder_id'])
        )
        if not result.scalar_one_or_none():
            crisis_dict['responder_id'] = None
    
    crisis = CrisisIntervention(**crisis_dict)
    db.add(crisis)
    await db.commit()
    await db.refresh(crisis)
    
    # Send emergency notifications
    if crisis.severity in ["High", "Emergency"]:
        await send_notification(
            user_id=crisis.user_id,
            title="Emergency Support Available",
            message="Emergency support is available. Please contact emergency services if needed.",
            notification_type="crisis"
        )
        
        if crisis.responder_id:
            await send_notification(
                user_id=crisis.responder.user_id,
                title="Emergency Intervention Required",
                message=f"Emergency intervention required for user ID {crisis.user_id}",
                notification_type="crisis"
            )
    
    return crisis

async def update_crisis_intervention(
    db: AsyncSession,
    crisis_id: int,
    update_data: CrisisInterventionUpdate
) -> Optional[CrisisIntervention]:
    """Update a crisis intervention record."""
    result = await db.execute(select(CrisisIntervention).where(CrisisIntervention.id == crisis_id))
    crisis = result.scalar_one_or_none()
    
    if not crisis:
        return None
    
    # Convert update data to dict and handle timezone-aware datetimes
    update_dict = update_data.dict(exclude_unset=True)
    if 'follow_up_date' in update_dict and update_dict['follow_up_date'] and update_dict['follow_up_date'].tzinfo is not None:
        update_dict['follow_up_date'] = update_dict['follow_up_date'].replace(tzinfo=None)
    
    for field, value in update_dict.items():
        setattr(crisis, field, value)
    
    await db.commit()
    await db.refresh(crisis)
    return crisis

# Resource Management
async def create_mental_health_resource(
    db: AsyncSession,
    resource_data: MentalHealthResourceCreate
) -> MentalHealthResource:
    """Create a new mental health resource."""
    resource = MentalHealthResource(**resource_data.dict())
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return resource

async def get_mental_health_resources(
    db: AsyncSession
) -> List[MentalHealthResource]:
    """Get all mental health resources."""
    query = select(MentalHealthResource)
    result = await db.execute(query)
    return result.scalars().all()

# Review Management
async def create_therapist_review(
    db: AsyncSession,
    review_data: TherapistReviewCreate
) -> TherapistReview:
    """Create a new therapist review."""
    review_dict = review_data.dict()
    
    # Handle timezone-aware datetimes
    if review_dict.get('session_date') and review_dict['session_date'].tzinfo is not None:
        review_dict['session_date'] = review_dict['session_date'].replace(tzinfo=None)
    
    # Convert enum values to uppercase for database compatibility
    if review_dict.get('therapy_type'):
        review_dict['therapy_type'] = review_dict['therapy_type'].value.upper()
    
    # Map therapy approach values to database enum values
    approach_mapping = {
        'cognitive_behavioral': 'CBT',
        'dialectical_behavioral': 'DBT',
        'psychodynamic': 'PSYCHODYNAMIC',
        'humanistic': 'HUMANISTIC',
        'mindfulness': 'MINDFULNESS',
        'other': 'OTHER'
    }
    if review_dict.get('approach'):
        approach_value = review_dict['approach'].value.lower()
        review_dict['approach'] = approach_mapping.get(approach_value, 'OTHER')
    
    review = TherapistReview(**review_dict)
    db.add(review)
    await db.commit()
    await db.refresh(review)
    
    # Update therapist rating
    therapist = await get_professional(db, review.therapist_id)
    if therapist:
        # Calculate new average rating
        result = await db.execute(
            select(func.avg(TherapistReview.rating))
            .where(TherapistReview.therapist_id == therapist.id)
        )
        new_rating = result.scalar_one() or 0.0
        therapist.rating = new_rating
        await db.commit()
    
    return review

async def update_review(
    db: AsyncSession,
    review_id: int,
    update_data: TherapistReviewUpdate
) -> Optional[TherapistReview]:
    """Update a therapist review."""
    result = await db.execute(select(TherapistReview).where(TherapistReview.id == review_id))
    review = result.scalar_one_or_none()
    
    if not review:
        return None
    
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(review, field, value)
    
    await db.commit()
    await db.refresh(review)
    return review

# History and Analytics
async def get_user_mental_health_history(
    db: AsyncSession,
    user_id: int,
    days: int = 30
) -> Dict[str, Any]:
    """Get comprehensive mental health history for a user."""
    since = datetime.utcnow() - timedelta(days=days)
    
    # Get assessments
    assessments_query = select(MentalHealthAssessment).where(
        and_(
            MentalHealthAssessment.user_id == user_id,
            MentalHealthAssessment.date >= since
        )
    )
    assessments_result = await db.execute(assessments_query)
    assessments = assessments_result.scalars().all()
    
    # Get crisis interventions
    crisis_query = select(CrisisIntervention).where(
        and_(
            CrisisIntervention.user_id == user_id,
            CrisisIntervention.date_time >= since
        )
    )
    crisis_result = await db.execute(crisis_query)
    crisis_interventions = crisis_result.scalars().all()
    
    # Get appointments
    appointments_query = select(TherapistAppointment).where(
        and_(
            TherapistAppointment.user_id == user_id,
            TherapistAppointment.date_time >= since
        )
    )
    appointments_result = await db.execute(appointments_query)
    appointments = appointments_result.scalars().all()
    
    # Get all resources
    resources_query = select(MentalHealthResource)
    resources_result = await db.execute(resources_query)
    resources = resources_result.scalars().all()
    
    return {
        "assessments": assessments,
        "crisis_interventions": crisis_interventions,
        "appointments": appointments,
        "resources_accessed": resources,
        "summary": {
            "total_assessments": len(assessments),
            "total_crisis_interventions": len(crisis_interventions),
            "total_appointments": len(appointments),
            "high_risk_assessments": len([a for a in assessments if a.risk_level == "High"]),
            "completed_appointments": len([a for a in appointments if a.status == "Completed"]),
            "upcoming_appointments": len([a for a in appointments if a.status == "Confirmed"])
        }
    } 