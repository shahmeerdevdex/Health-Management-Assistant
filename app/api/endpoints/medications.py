from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.db.session import get_db
from app.schemas.medication import MedicationCreate, MedicationResponse, MedicationUpdate
from app.crud.medication import create_medication, get_medications, update_medication, delete_medication
from app.api.endpoints.dependencies import get_current_user  

router = APIRouter()

@router.post("/add", response_model=MedicationResponse)
async def add_medication_endpoint(
    medication: MedicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)  
):
    """
    Add a new medication for a user.

    Args:
        medication (MedicationCreate): The medication details including name, dosage, and schedule.
        db (AsyncSession): Database session dependency.
        current_user (User): The authenticated user.

    Returns:
        MedicationResponse: The created medication record.
    """
    return await create_medication(db, medication)

@router.get("/", response_model=list[MedicationResponse])
async def get_medications_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)  
):
    """
    Retrieve a list of medications for the authenticated user.

    Args:
        db (AsyncSession): Database session dependency.
        current_user (User): The authenticated user.

    Returns:
        list[MedicationResponse]: A list of the user's medications.
    """
    return await get_medications(db, current_user.id)  

@router.put("/mark-taken/{medication_id}")
async def mark_medication_taken_endpoint(
    medication_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)  
):
    """
    Mark a medication as taken.

    Args:
        medication_id (int): The ID of the medication to mark as taken.
        db (AsyncSession): Database session dependency.
        current_user (User): The authenticated user.

    Returns:
        Updated medication record.
    """
    med_update = MedicationUpdate(start_date=datetime.utcnow())  
    return await update_medication(db, medication_id, med_update)

@router.delete("/delete/{medication_id}")
async def delete_medication_endpoint(
    medication_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)  
):
    """
    Delete a medication from the user's list.

    Args:
        medication_id (int): The ID of the medication to be deleted.
        db (AsyncSession): Database session dependency.
        current_user (User): The authenticated user.

    Returns:
        Deletion confirmation message.
    """
    return await delete_medication(db, medication_id)
