from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.ehr_sync import EHRSyncRequest, EHRSyncResponse
from app.crud.ehr_sync import get_ehr_record_by_user_id, upsert_ehr_record
from app.api.endpoints.dependencies import get_current_user
from app.db.models.user import User

router = APIRouter()

@router.get("/sync/{user_id}", response_model=EHRSyncResponse)
async def fetch_ehr_data(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve EHR record for a specific user.
    """
    record = await get_ehr_record_by_user_id(db, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="No EHR record found.")
    return EHRSyncResponse(
        ehr_id=f"EHR-{record.user_id}",
        medical_history=record.medical_history,
        last_updated=record.last_synced.strftime("%Y-%m-%d")
    )


@router.post("/sync", response_model=EHRSyncResponse)
async def sync_ehr_data(
    ehr_data: EHRSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create or update EHR data for a user.
    """
    # Optional: validate permissions (e.g., only practitioners or the user themselves)
    if current_user.id != ehr_data.user_id and current_user.role != "PRACTITIONER":
        raise HTTPException(status_code=403, detail="Not authorized to sync this user's EHR.")

    record = await upsert_ehr_record(db, ehr_data)

    return EHRSyncResponse(
        ehr_id=f"EHR-{record.user_id}",
        medical_history=record.medical_history,
        last_updated=record.last_synced.strftime("%Y-%m-%d")
    )
