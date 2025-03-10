from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.medication import MedicationCreate, MedicationResponse, MedicationUpdate
from app.crud.medication import create_medication, get_medications, update_medication, delete_medication
from app.services.auth_service import verify_access_token  
from datetime import datetime

router = APIRouter()

@router.post("/medications/add", response_model=MedicationResponse, dependencies=[Depends(verify_access_token)])
async def add_medication_endpoint(medication: MedicationCreate, db: AsyncSession = Depends(get_db)):
    """
    Add a new medication for a user.

    Args:
        medication (MedicationCreate): The medication details including name, dosage, and schedule.
        db (AsyncSession): Database session dependency.

    Returns:
        MedicationResponse: The created medication record.
    """
    return await create_medication(db, medication) 

@router.get("/medications/{user_id}", response_model=list[MedicationResponse], dependencies=[Depends(verify_access_token)])
async def get_medications_endpoint(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a list of medications for a specific user.

    Args:
        user_id (int): The ID of the user whose medications need to be fetched.
        db (AsyncSession): Database session dependency.

    Returns:
        list[MedicationResponse]: A list of the user's medications.
    """
    return await get_medications(db, user_id)

@router.put("/medications/mark-taken/{medication_id}", dependencies=[Depends(verify_access_token)])
async def mark_medication_taken_endpoint(medication_id: int, db: AsyncSession = Depends(get_db)):
    """
    Mark a medication as taken.

    Args:
        medication_id (int): The ID of the medication to mark as taken.
        db (AsyncSession): Database session dependency.

    Returns:
        Updated medication record.
    """
    med_update = MedicationUpdate(start_date=datetime.utcnow())  # Example: Updating the start_date
    return await update_medication(db, medication_id, med_update)

@router.delete("/medications/delete/{medication_id}", dependencies=[Depends(verify_access_token)])
async def delete_medication_endpoint(medication_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a medication from the user's list.

    Args:
        medication_id (int): The ID of the medication to be deleted.
        db (AsyncSession): Database session dependency.

    Returns:
        Deletion confirmation message.
    """
    return await delete_medication(db, medication_id)
