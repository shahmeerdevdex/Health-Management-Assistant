from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.marketplace import MentalHealthMarketplaceRequest, MentalHealthMarketplaceResponse
from app.services.marketplace_service import process_mental_health_marketplace
from app.api.endpoints.dependencies import get_db,get_current_user

router = APIRouter()

@router.post("/mental-health", response_model=MentalHealthMarketplaceResponse)
async def mental_health_marketplace(
    request: MentalHealthMarketplaceRequest,
    db: Session = Depends(get_db),
    db_user = Depends(get_current_user)
):
    """
    Provides access to mental health professionals and services available in the marketplace.
    """
    try:
        marketplace_data = await process_mental_health_marketplace(request, db)
        return marketplace_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
