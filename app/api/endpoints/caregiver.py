from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.schemas.caregiver import CaregiverRequest, CaregiverResponse, CaregiverAssignmentResponse,CaregiverProfileResponse
from app.services.caregiver_service import process_caregiver_management
from app.api.endpoints.dependencies import get_db, get_current_user
from app.db.models.caregiver import CaregiverAssignment,Caregiver
from app.db.models.user import User, UserRoleEnum

router = APIRouter()

@router.post("/management", response_model=CaregiverResponse)
async def caregiver_management(
    request: CaregiverRequest,
    db: AsyncSession = Depends(get_db),
    db_user=Depends(get_current_user)
):
    """
    Manages caregiver support tools, including scheduling, medication tracking, and assistance coordination.
    """

    # Restrict to primary account holders only
    if db_user.role != UserRoleEnum.PRIMARY_HOLDER:
        raise HTTPException(status_code=403, detail="Only Primary Account Holders can manage caregivers.")

    # Validate caregiver_id exists
    caregiver_result = await db.execute(select(User).where(User.id == request.user_id))
    caregiver = caregiver_result.scalars().first()
    if not caregiver:
        raise HTTPException(status_code=404, detail=f"Caregiver user_id {request.user_id} not found")

    # Validate patient_id exists
    patient_result = await db.execute(select(User).where(User.id == request.patient_id))
    patient = patient_result.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient user_id {request.patient_id} not found")

    # Optional: prevent assigning user to themselves
    if request.user_id == request.patient_id:
        raise HTTPException(status_code=400, detail="A user cannot be assigned as their own caregiver.")

    # Proceed with processing
    try:
        caregiver_data = await process_caregiver_management(request, db)
        return caregiver_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/caregivers/{user_id}/profile", response_model=CaregiverProfileResponse)
async def get_caregiver_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve caregiver profile information by user ID.
    """
    result = await db.execute(select(Caregiver).where(Caregiver.user_id == user_id))
    caregiver = result.scalars().first()

    if not caregiver:
        raise HTTPException(status_code=404, detail="Caregiver profile not found.")

    return caregiver