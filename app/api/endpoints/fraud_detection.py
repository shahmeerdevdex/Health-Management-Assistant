from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.fraud_detection import FraudDetectionRequest, FraudDetectionResponse
from app.services.fraud_detection_service import process_fraud_detection
from app.api.endpoints.dependencies import get_db, get_current_user
from app.db.models.user import UserRoleEnum

router = APIRouter()

@router.post("/fraud-detection", response_model=FraudDetectionResponse)
async def fraud_detection(
    request: FraudDetectionRequest,
    db: AsyncSession = Depends(get_db),
    db_user = Depends(get_current_user)
):
    """
    Analyzes transactions and detects potential fraudulent activities in health-related claims.
    Only Primary Account Holders (PAH) can access this feature.
    """
    # Restrict access to Primary Account Holders (PAH) only
    if db_user.role != UserRoleEnum.PRIMARY_HOLDER:
        raise HTTPException(status_code=403, detail="Only Primary Account Holders can access fraud detection.")

    try:
        fraud_analysis = await process_fraud_detection(request, db)
        return fraud_analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
