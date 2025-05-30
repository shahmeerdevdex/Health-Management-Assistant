from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.appointment import (
    AppointmentCreate, 
    AppointmentResponse, 
    AppointmentUpdate,
    AppointmentFilter,
    ProviderAppointmentSummary,
    AppointmentStatus,
    AppointmentType
)
from app.crud.appointment import (
    create_appointment, 
    get_appointments, 
    delete_appointment, 
    update_appointment,
    get_upcoming_appointments,
    get_provider_appointments,
    get_provider_summary,
    get_appointment_history
)
from app.api.endpoints.dependencies import get_current_user 
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.db.models.appointments import ProviderType

router = APIRouter()

@router.post("/add", response_model=AppointmentResponse)
async def add_appointment_endpoint(
    appointment: AppointmentCreate, 
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)  
):
    """
    Create a new appointment for the authenticated user.
    
    Features:
    - Support for both practitioners and professionals
    - Appointment type specification
    - Duration tracking
    - Session notes and goals
    - Follow-up scheduling
    """
    try:
        return await create_appointment(db, current_user.id, appointment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/list", response_model=List[AppointmentResponse])
async def list_appointments_endpoint(
    filters: AppointmentFilter = Depends(),
    db: AsyncSession = Depends(get_db), 
    current_user=Depends(get_current_user)  
):
    """
    Retrieve appointments with advanced filtering.
    
    Filters:
    - Date range (start_date, end_date)
    - Status (scheduled, confirmed, completed, cancelled, rescheduled)
    - Appointment type (regular, follow-up, emergency)
    - Provider type (practitioner/professional)
    - Provider ID
    """
    # Convert timezone-aware datetimes to timezone-naive
    if filters.start_date and filters.start_date.tzinfo is not None:
        filters.start_date = filters.start_date.astimezone().replace(tzinfo=None)
    if filters.end_date and filters.end_date.tzinfo is not None:
        filters.end_date = filters.end_date.astimezone().replace(tzinfo=None)
    
    return await get_appointments(db, current_user.id, filters)

@router.get("/upcoming", response_model=List[AppointmentResponse])
async def get_upcoming_appointments_endpoint(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get upcoming appointments for the next specified number of days.
    """
    return await get_upcoming_appointments(db, current_user.id, days)

@router.get("/provider/{provider_type}/{provider_id}", response_model=List[AppointmentResponse])
async def get_provider_appointments_endpoint(
    provider_type: ProviderType,
    provider_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get appointments for a specific provider (practitioner or professional).
    """
    # Convert timezone-aware datetimes to timezone-naive
    if start_date and start_date.tzinfo is not None:
        start_date = start_date.astimezone().replace(tzinfo=None)
    if end_date and end_date.tzinfo is not None:
        end_date = end_date.astimezone().replace(tzinfo=None)
    
    return await get_provider_appointments(db, provider_type, provider_id, start_date, end_date)

@router.get("/provider/{provider_type}/{provider_id}/summary", response_model=ProviderAppointmentSummary)
async def get_provider_summary_endpoint(
    provider_type: ProviderType,
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get appointment summary for a provider.
    
    Summary includes:
    - Total appointments
    - Upcoming appointments
    - Completed appointments
    - Cancelled appointments
    - Average rating
    """
    return await get_provider_summary(db, provider_type, provider_id)

@router.get("/history", response_model=Dict[str, Any])
async def get_appointment_history_endpoint(
    days: int = Query(365, ge=1, le=3650),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get appointment history with analytics.
    
    Analytics include:
    - Total appointments
    - Completed appointments
    - Cancelled appointments
    - Completion rate
    """
    return await get_appointment_history(db, current_user.id, days)

@router.delete("/delete/{appointment_id}")
async def delete_appointment_endpoint(
    appointment_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user=Depends(get_current_user) 
):
    """
    Delete an appointment by ID.
    """
    deleted_appointment = await delete_appointment(db, appointment_id)
    
    if not deleted_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return {"message": "Appointment deleted successfully"}

@router.put("/update/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment_endpoint(
    appointment_id: int,
    appointment_update: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)  
):
    """
    Update an existing appointment.
    
    Features:
    - Status updates
    - Session notes
    - Follow-up scheduling
    - Goals and homework tracking
    """
    try:
        updated_appointment = await update_appointment(db, appointment_id, appointment_update)
        
        if not updated_appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")

        return updated_appointment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
