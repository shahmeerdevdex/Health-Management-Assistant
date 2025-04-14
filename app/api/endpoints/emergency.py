from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.emergency import EmergencySupportRequest, EmergencySupportResponse
from app.services.emergency_service import process_emergency_support
from app.api.endpoints.dependencies import get_db,get_current_user

router = APIRouter()

@router.post("/support", response_model=EmergencySupportResponse)
async def emergency_support(
    request: EmergencySupportRequest,
    db: Session = Depends(get_db),
    db_user = Depends(get_current_user)
):
    """
    Provides immediate crisis support recommendations and emergency contacts.
    """
    try:
        support_data = await process_emergency_support(request, db)
        return support_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
