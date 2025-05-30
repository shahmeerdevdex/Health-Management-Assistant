from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from app.db.models.appointments import Appointment, AppointmentStatus, AppointmentType, ProviderType
from app.schemas.appointment import AppointmentCreate, AppointmentResponse,AppointmentUpdate, AppointmentFilter, ProviderAppointmentSummary
from datetime import datetime, timedelta
from app.db.models.practitioners import Practitioner
from app.db.models.mental_health import Professional

async def create_appointment(db: AsyncSession, user_id: int, app: AppointmentCreate):
    """Create a new appointment with enhanced features."""
    
    # Convert timezone-aware datetime to timezone-naive UTC
    appointment_date = app.date
    if appointment_date.tzinfo is not None:
        appointment_date = appointment_date.astimezone().replace(tzinfo=None)
    
    # Convert follow-up date if it exists and is timezone-aware
    follow_up_date = app.follow_up_date
    if follow_up_date and follow_up_date.tzinfo is not None:
        follow_up_date = follow_up_date.astimezone().replace(tzinfo=None)
    
    # Verify provider exists based on type
    if app.provider_type == ProviderType.PRACTITIONER:
        provider = await db.execute(
            select(Practitioner).filter(Practitioner.id == app.provider_id)
        )
    else:
        provider = await db.execute(
            select(Professional).filter(Professional.id == app.provider_id)
        )
    
    if not provider.scalar_one_or_none():
        raise ValueError(f"{app.provider_type.value.capitalize()} not found")

    # Check for scheduling conflicts
    existing_appointment = await db.execute(
        select(Appointment).filter(
            and_(
                Appointment.provider_type == app.provider_type,
                Appointment.provider_id == app.provider_id,
                Appointment.date == appointment_date,
                Appointment.status != AppointmentStatus.CANCELLED
            )
        )
    )
    if existing_appointment.scalars().first():
        raise ValueError("Time slot is already booked")

    appointment = Appointment(
        user_id=user_id,
        provider_type=app.provider_type,
        provider_id=app.provider_id,
        date=appointment_date,
        duration=app.duration,
        location=app.location,
        appointment_type=app.appointment_type,
        notes=app.notes,
        follow_up_required=app.follow_up_required,
        follow_up_date=follow_up_date,
        session_summary=app.session_summary,
        goals_discussed=app.goals_discussed,
        homework_assigned=app.homework_assigned,
        next_session_agenda=app.next_session_agenda,
        video_call_link=app.video_call_link
    )

    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)
    
    return AppointmentResponse.model_validate(appointment)

async def get_appointment(db: AsyncSession, appointment_id: int):
    """Retrieve a specific appointment by ID."""
    result = await db.execute(select(Appointment).filter(Appointment.id == appointment_id))
    return result.scalars().first()

async def get_appointments(
    db: AsyncSession, 
    user_id: int, 
    filters: AppointmentFilter = None
):
    """Retrieve appointments with filtering options."""
    query = select(Appointment).filter(Appointment.user_id == user_id)
    
    if filters:
        if filters.start_date:
            query = query.filter(Appointment.date >= filters.start_date)
        if filters.end_date:
            query = query.filter(Appointment.date <= filters.end_date)
        if filters.status:
            query = query.filter(Appointment.status == filters.status)
        if filters.appointment_type:
            query = query.filter(Appointment.appointment_type == filters.appointment_type)
        if filters.provider_type:
            query = query.filter(Appointment.provider_type == filters.provider_type)
        if filters.provider_id:
            query = query.filter(Appointment.provider_id == filters.provider_id)
    
    query = query.order_by(Appointment.date)
    result = await db.execute(query)
    return result.scalars().all()

async def get_provider_appointments(
    db: AsyncSession,
    provider_type: ProviderType,
    provider_id: int,
    start_date: datetime = None,
    end_date: datetime = None
):
    """Get appointments for a specific provider (practitioner or professional)."""
    query = select(Appointment).filter(
        and_(
            Appointment.provider_type == provider_type,
            Appointment.provider_id == provider_id
        )
    )
    
    if start_date:
        query = query.filter(Appointment.date >= start_date)
    if end_date:
        query = query.filter(Appointment.date <= end_date)
        
    query = query.order_by(Appointment.date)
    result = await db.execute(query)
    return result.scalars().all()

async def get_provider_summary(
    db: AsyncSession,
    provider_type: ProviderType,
    provider_id: int
) -> ProviderAppointmentSummary:
    """Get appointment summary for a provider."""
    appointments = await get_provider_appointments(db, provider_type, provider_id)
    
    # Get provider name
    if provider_type == ProviderType.PRACTITIONER:
        provider = await db.execute(
            select(Practitioner).filter(Practitioner.id == provider_id)
        )
        provider_name = provider.scalar_one_or_none().name
    else:
        provider = await db.execute(
            select(Professional).filter(Professional.id == provider_id)
        )
        provider_name = provider.scalar_one_or_none().name

    total_appointments = len(appointments)
    upcoming_appointments = sum(1 for a in appointments if a.date > datetime.utcnow() and a.status != AppointmentStatus.CANCELLED)
    completed_appointments = sum(1 for a in appointments if a.status == AppointmentStatus.COMPLETED)
    cancelled_appointments = sum(1 for a in appointments if a.status == AppointmentStatus.CANCELLED)

    return ProviderAppointmentSummary(
        provider_id=provider_id,
        provider_type=provider_type,
        provider_name=provider_name,
        total_appointments=total_appointments,
        upcoming_appointments=upcoming_appointments,
        completed_appointments=completed_appointments,
        cancelled_appointments=cancelled_appointments
    )

async def delete_appointment(db: AsyncSession, appointment_id: int):
    """Delete an appointment by ID."""
    appointment = await get_appointment(db, appointment_id)
    if appointment:
        await db.delete(appointment)
        await db.commit()
    return appointment

async def update_appointment(
    db: AsyncSession, 
    appointment_id: int, 
    appointment_update: AppointmentUpdate
):
    """Update an existing appointment with enhanced features."""
    result = await db.execute(select(Appointment).filter(Appointment.id == appointment_id))
    appointment = result.scalars().first()

    if not appointment:
        return None

    # Convert timezone-aware datetime to timezone-naive UTC if date is being updated
    if appointment_update.date:
        appointment_date = appointment_update.date
        if appointment_date.tzinfo is not None:
            appointment_date = appointment_date.astimezone().replace(tzinfo=None)
        appointment_update.date = appointment_date

    # Convert follow-up date if it exists and is timezone-aware
    if appointment_update.follow_up_date:
        follow_up_date = appointment_update.follow_up_date
        if follow_up_date.tzinfo is not None:
            follow_up_date = follow_up_date.astimezone().replace(tzinfo=None)
        appointment_update.follow_up_date = follow_up_date

    # Update fields if provided
    for field, value in appointment_update.model_dump(exclude_unset=True).items():
        setattr(appointment, field, value)

    # If date is being updated, check for conflicts
    if appointment_update.date:
        existing_appointment = await db.execute(
            select(Appointment).filter(
                and_(
                    Appointment.provider_type == appointment.provider_type,
                    Appointment.provider_id == appointment.provider_id,
                    Appointment.date == appointment_update.date,
                    Appointment.id != appointment_id,
                    Appointment.status != AppointmentStatus.CANCELLED
                )
            )
        )
        if existing_appointment.scalars().first():
            raise ValueError("Time slot is already booked")

    await db.commit()
    await db.refresh(appointment)
    return AppointmentResponse.model_validate(appointment)

async def get_upcoming_appointments(
    db: AsyncSession, 
    user_id: int,
    days: int = 30
):
    """Retrieve upcoming appointments for a user."""
    end_date = datetime.utcnow() + timedelta(days=days)
    result = await db.execute(
        select(Appointment)
        .filter(
            and_(
                Appointment.user_id == user_id,
                Appointment.date >= datetime.utcnow(),
                Appointment.date <= end_date,
                Appointment.status != AppointmentStatus.CANCELLED
            )
        )
        .order_by(Appointment.date)
    )
    return result.scalars().all()

async def get_appointment_history(
    db: AsyncSession,
    user_id: int,
    days: int = 365
):
    """Get appointment history with analytics."""
    start_date = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(Appointment)
        .filter(
            and_(
                Appointment.user_id == user_id,
                Appointment.date >= start_date
            )
        )
        .order_by(Appointment.date.desc())
    )
    appointments = result.scalars().all()
    
    # Calculate analytics
    total_appointments = len(appointments)
    completed_appointments = sum(1 for a in appointments if a.status == AppointmentStatus.COMPLETED)
    cancelled_appointments = sum(1 for a in appointments if a.status == AppointmentStatus.CANCELLED)
    
    # Convert appointments to Pydantic models
    appointment_responses = [AppointmentResponse.model_validate(appointment) for appointment in appointments]
    
    return {
        "appointments": appointment_responses,
        "analytics": {
            "total_appointments": total_appointments,
            "completed_appointments": completed_appointments,
            "cancelled_appointments": cancelled_appointments,
            "completion_rate": (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0
        }
    }
