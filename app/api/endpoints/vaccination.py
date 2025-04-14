from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.vaccination import (
    VaccinationRecordRequest,
    VaccinationRecordResponse,
    VaccinationRemindersResponse,
    VaccinationReminder
)
from app.services.vaccination_service import (
    process_vaccination_record,
    get_vaccination_record,
    update_vaccination_record,
    delete_vaccination_record,
    get_vaccination_reminders,
    sync_national_vaccine_records
)
from app.api.endpoints.dependencies import get_db, get_current_user

router = APIRouter()

@router.post("/tracker", response_model=VaccinationRecordResponse)
async def vaccination_tracker(
    request: VaccinationRecordRequest,
    db: Session = Depends(get_db),
    db_user = Depends(get_current_user)
):
    """
    Stores vaccination records and provides tracking information.
    """
    try:
        record_data = await process_vaccination_record(request, db)
        return record_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tracker/{record_id}", response_model=VaccinationRecordResponse)
async def get_vaccination(record_id: int, db: Session = Depends(get_db), db_user = Depends(get_current_user)):
    """
    Retrieves a vaccination record by ID.
    """
    record = await get_vaccination_record(record_id, db)
    if not record:
        raise HTTPException(status_code=404, detail="Vaccination record not found")
    return record

@router.put("/tracker/{record_id}", response_model=VaccinationRecordResponse)
async def update_vaccination(
    record_id: int,
    request: VaccinationRecordRequest,
    db: Session = Depends(get_db),
    db_user = Depends(get_current_user)
):
    """
    Updates an existing vaccination record.
    """
    updated_record = await update_vaccination_record(record_id, request, db)
    if not updated_record:
        raise HTTPException(status_code=404, detail="Vaccination record not found or update failed")
    return updated_record

@router.delete("/tracker/{record_id}")
async def delete_vaccination(record_id: int, db: Session = Depends(get_db), db_user = Depends(get_current_user)):
    """
    Deletes a vaccination record by ID.
    """
    success = await delete_vaccination_record(record_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Vaccination record not found or delete failed")
    return {"message": "Vaccination record deleted successfully"}

@router.get("/reminders/{user_id}", response_model=VaccinationRemindersResponse)
async def vaccination_reminders(user_id: int, db: Session = Depends(get_db), db_user = Depends(get_current_user)):
    """
    Retrieves upcoming vaccination reminders for a user.
    """
    reminders: List[VaccinationReminder] = await get_vaccination_reminders(user_id, db)

    if not reminders:
        raise HTTPException(status_code=404, detail="No upcoming vaccinations found")

    return VaccinationRemindersResponse(user_id=user_id, reminders=reminders)

@router.post("/sync-national-records")
async def sync_national_vaccination_records(
    user_id: int,
    db: Session = Depends(get_db),
    db_user = Depends(get_current_user)
):
    """
    Sync user vaccination records with national immunization systems.
    """
    try:
        synced_records = await sync_national_vaccine_records(user_id, db)
        return {"message": "Vaccination records synced successfully", "records": synced_records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
