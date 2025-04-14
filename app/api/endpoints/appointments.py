from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.appointment import AppointmentCreate, AppointmentResponse, AppointmentUpdate
from app.crud.appointment import create_appointment, get_appointments, delete_appointment, update_appointment
from app.api.endpoints.dependencies import get_current_user 
from typing import List

router = APIRouter()

@router.post("/add", response_model=AppointmentResponse)
async def add_appointment_endpoint(
    appointment: AppointmentCreate, 
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)  
):
    """
    Create a new appointment for the authenticated user.

    - Requires authentication via access token.
    - Creates a new appointment.
    - Returns the created appointment details.
    """
    return await create_appointment(db, current_user.id, appointment)

@router.get("/{user_id}", response_model=List[AppointmentResponse])
async def get_appointments_endpoint(
    user_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user=Depends(get_current_user)  
):
    """
    Retrieve all appointments for the authenticated user.

    - Requires authentication via access token.
    - Returns a list of appointments for the authenticated user.
    """
    return await get_appointments(db, user_id)

@router.delete("/delete/{appointment_id}")
async def delete_appointment_endpoint(
    appointment_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user=Depends(get_current_user) 
):
    """
    Delete an appointment by ID.

    - Requires authentication via access token.
    - Deletes the specified appointment if found.
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

    - Requires authentication via access token.
    - Updates the specified appointment if found.
    - Returns the updated appointment details.
    """
    updated_appointment = await update_appointment(db, appointment_id, appointment_update)
    
    if not updated_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return updated_appointment
