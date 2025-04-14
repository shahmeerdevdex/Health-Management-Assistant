from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.sustainability import SustainabilityRequest, SustainabilityResponse
from app.services.sustainability_service import process_sustainability_data
from app.api.endpoints.dependencies import get_db,get_current_user

router = APIRouter()

@router.post("/sustainability", response_model=SustainabilityResponse)
async def sustainability_initiatives(
    request: SustainabilityRequest,
    db: Session = Depends(get_db),
    db_user = Depends(get_current_user)
):
    """
    Provides insights on sustainable and ethical health practices.
    """
    try:
        sustainability_data = await process_sustainability_data(request, db)
        return sustainability_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
