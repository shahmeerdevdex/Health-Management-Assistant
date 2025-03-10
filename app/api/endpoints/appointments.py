from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.appointment import AppointmentCreate, AppointmentResponse, AppointmentUpdate
from app.crud.appointment import create_appointment, get_appointments, delete_appointment, update_appointment
from app.services.auth_service import verify_access_token  # Import authentication dependency
from app.schemas.user import UserCreate   # Assuming user schema is defined for authentication

router = APIRouter()

@router.post("/appointments/add", response_model=AppointmentResponse, dependencies=[Depends(verify_access_token)])
async def add_appointment_endpoint(
    appointment: AppointmentCreate, 
    db: Session = Depends(get_db),
    current_user: UserCreate = Depends(verify_access_token)
):
    """
    Create a new appointment for the authenticated user.

    - **Requires Authentication** 
    - **Parameters:** 
        - `appointment`: AppointmentCreate schema containing doctor name, date, location.
    - **Returns:** 
        - `AppointmentResponse`: Created appointment details.
    """
    return await create_appointment(db, current_user.id, appointment)

@router.get("/appointments/{user_id}", response_model=list[AppointmentResponse], dependencies=[Depends(verify_access_token)])
async def get_appointments_endpoint(
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: UserCreate = Depends(verify_access_token)
):
    """
    Retrieve all appointments for a given user.

    - **Requires Authentication** 
    - **Parameters:** 
        - `user_id`: ID of the user whose appointments to fetch.
    - **Returns:** 
        - `List[AppointmentResponse]`: List of appointments for the user.
    """
    return await get_appointments(db, user_id)

@router.delete("/appointments/delete/{appointment_id}", dependencies=[Depends(verify_access_token)])
async def delete_appointment_endpoint(
    appointment_id: int, 
    db: Session = Depends(get_db), 
    current_user: UserCreate = Depends(verify_access_token)
):
    """
    Delete an appointment by ID.

    - **Requires Authentication** 
    - **Parameters:** 
        - `appointment_id`: ID of the appointment to delete.
    - **Returns:** 
        - `Success message` if deleted.
    """
    deleted_appointment = await delete_appointment(db, appointment_id)
    if not deleted_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Appointment deleted successfully"}

@router.put("/appointments/update/{appointment_id}", response_model=AppointmentResponse, dependencies=[Depends(verify_access_token)])
async def update_appointment_endpoint(
    appointment_id: int,
    appointment_update: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: UserCreate = Depends(verify_access_token)
):
    """
    Update an existing appointment.

    - **Requires Authentication** 
    - **Parameters:** 
        - `appointment_id`: ID of the appointment to update.
        - `appointment_update`: Data to update.
    - **Returns:** 
        - `Updated AppointmentResponse` if successful.
    """
    updated_appointment = await update_appointment(db, appointment_id, appointment_update)
    if not updated_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return updated_appointment
