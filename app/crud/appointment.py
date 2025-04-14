from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.appointments import Appointment
from app.schemas.appointment import AppointmentCreate, AppointmentResponse
from datetime import datetime

async def create_appointment(db: AsyncSession, user_id: int, app: AppointmentCreate):
    """Create a new appointment, ensuring datetime is naive (no timezone)."""
    
    appointment_date = app.date
    if appointment_date.tzinfo is not None:
        appointment_date = appointment_date.astimezone().replace(tzinfo=None)

    appointment = Appointment(
        user_id=user_id, 
        doctor_name=app.doctor_name, 
        date=appointment_date,  
        location=app.location
    )

    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)

    
    return AppointmentResponse(
        id=appointment.id,
        user_id=appointment.user_id,
        doctor_name=appointment.doctor_name,
        date=appointment.date,
        location=appointment.location
    )

async def get_appointment(db: AsyncSession, appointment_id: int):
    """Retrieve a specific appointment by ID."""
    result = await db.execute(select(Appointment).filter(Appointment.id == appointment_id))
    return result.scalars().first()

async def get_appointments(db: AsyncSession, user_id: int):
    """Retrieve all appointments for a given user."""
    result = await db.execute(select(Appointment).filter(Appointment.user_id == user_id))
    return result.scalars().all()

async def delete_appointment(db: AsyncSession, appointment_id: int):
    """Delete an appointment by ID."""
    appointment = await get_appointment(db, appointment_id)
    if appointment:
        await db.delete(appointment)
        await db.commit()
    return appointment

async def update_appointment(db: AsyncSession, appointment_id: int, appointment_update: AppointmentCreate):
    """Update an existing appointment."""
    result = await db.execute(select(Appointment).filter(Appointment.id == appointment_id))
    appointment = result.scalars().first()

    if not appointment:
        return None 

    if appointment_update.doctor_name is not None:
        appointment.doctor_name = appointment_update.doctor_name
    if appointment_update.date is not None:
        # Convert to naive datetime
        appointment_date = appointment_update.date
        if appointment_date.tzinfo is not None:
            appointment_date = appointment_date.astimezone().replace(tzinfo=None)
        appointment.date = appointment_date
    if appointment_update.location is not None:
        appointment.location = appointment_update.location

    await db.commit()
    await db.refresh(appointment)

    return AppointmentResponse(
        id=appointment.id,
        user_id=appointment.user_id,
        doctor_name=appointment.doctor_name,
        date=appointment.date,
        location=appointment.location
    )

async def get_upcoming_appointments(db: AsyncSession, user_id: int):
    """
    Retrieve upcoming appointments for a user (from now into the future).
    """
    now = datetime.utcnow()

    stmt = (
        select(Appointment)
        .where(
            Appointment.user_id == user_id,
            Appointment.date >= now
        )
        .order_by(Appointment.date.asc())
        .limit(5)  # optionally limit to next 5
    )
    result = await db.execute(stmt)
    return result.scalars().all()
