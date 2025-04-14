from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.insurance import InsuranceCreate, InsuranceResponse
from app.crud.insurance import add_insurance_plan, get_insurance_plans, update_insurance_plan, delete_insurance_plan,verify_insurance_coverage
from app.api.endpoints.dependencies import get_current_user
from typing import List
from fastapi.responses import JSONResponse
from utils.insurance_card import generate_wallet_card_json
from app.db.models.insurance import InsurancePlan
from sqlalchemy.future import select

router = APIRouter()

@router.post("/add", response_model=InsuranceResponse)
async def add_insurance(
    insurance: InsuranceCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Add a new insurance plan."""
    return await add_insurance_plan(db, current_user.id, insurance)

@router.get("/{user_id}", response_model=List[InsuranceResponse])
async def get_insurance(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Fetch insurance plans for a user."""
    return await get_insurance_plans(db, user_id)

@router.put("/update/{insurance_id}", response_model=InsuranceResponse)
async def update_insurance(
    insurance_id: int,
    insurance: InsuranceCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Update an insurance plan."""
    updated_plan = await update_insurance_plan(db, insurance_id, insurance)

    if not updated_plan:
        raise HTTPException(status_code=404, detail="Insurance plan not found")

    return updated_plan

@router.delete("/delete/{insurance_id}")
async def delete_insurance(
    insurance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Delete an insurance plan."""
    deleted_plan = await delete_insurance_plan(db, insurance_id)

    if not deleted_plan:
        raise HTTPException(status_code=404, detail="Insurance plan not found")

    return {"message": "Insurance plan deleted successfully"}


@router.post("/verify/{insurance_id}", response_model=InsuranceResponse)
async def verify_insurance(
    insurance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Simulate insurance plan verification."""
    verified = await verify_insurance_coverage(db, insurance_id)
    if not verified:
        raise HTTPException(status_code=404, detail="Insurance plan not found.")
    return verified


@router.get("/wallet/export/{insurance_id}")
async def export_digital_wallet_card(
    insurance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Export a digital wallet-friendly JSON card for Apple/Google Wallet."""
    result = await db.execute(select(InsurancePlan).filter(InsurancePlan.id == insurance_id))
    insurance = result.scalars().first()
    if not insurance:
        raise HTTPException(status_code=404, detail="Insurance plan not found")

    card = generate_wallet_card_json(insurance)
    return JSONResponse(content=card)
