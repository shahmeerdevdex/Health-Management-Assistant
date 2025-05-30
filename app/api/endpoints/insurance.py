from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.insurance import InsuranceCreate, InsuranceResponse, OutOfPocketCostCreate, OutOfPocketCostResponse, MedicareClaimCreate, MedicareClaimResponse, InsuranceCoverageDetailCreate, InsuranceCoverageDetailResponse
from app.crud.insurance import add_insurance_plan, get_insurance_plans, update_insurance_plan, delete_insurance_plan, add_out_of_pocket_cost, add_medicare_claim, add_coverage_detail
from app.api.endpoints.dependencies import get_current_user
from app.services.insurance_provider_service import InsuranceProviderService
from app.services.digital_wallet_service import DigitalWalletService
from typing import List
from fastapi.responses import JSONResponse
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
    # Create insurance provider service
    provider_service = InsuranceProviderService()
    
    try:
        # Split full_name into first_name and last_name
        name_parts = current_user.full_name.split()
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        # Verify coverage with insurance provider
        verification_result = await provider_service.verify_coverage(
            policy_number=insurance.policy_number,
            member_id=current_user.id,
            date_of_birth=current_user.date_of_birth,
            first_name=first_name,
            last_name=last_name
        )

        # Add insurance plan to database
        insurance_plan = await add_insurance_plan(db, current_user.id, insurance)
        
        # Get coverage details from provider
        coverage_details = await provider_service.get_coverage_details(
            policy_number=insurance.policy_number,
            member_id=current_user.id
        )

        # Add coverage details
        await add_coverage_detail(
            db,
            InsuranceCoverageDetailCreate(
                insurance_plan_id=insurance_plan.id,
                coverage_type="comprehensive",
                benefits=coverage_details.get("benefits"),
                exclusions=coverage_details.get("exclusions")
            )
        )

        await provider_service.close()
        return insurance_plan

    except Exception as e:
        await provider_service.close()
        raise HTTPException(status_code=500, detail=str(e))

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
    provider_service = InsuranceProviderService()
    
    try:
        # Split full_name into first_name and last_name
        name_parts = current_user.full_name.split()
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        # Verify coverage with insurance provider
        verification_result = await provider_service.verify_coverage(
            policy_number=insurance.policy_number,
            member_id=current_user.id,
            date_of_birth=current_user.date_of_birth,
            first_name=first_name,
            last_name=last_name
        )

        # Update insurance plan
        updated_plan = await update_insurance_plan(db, insurance_id, insurance)

        if not updated_plan:
            raise HTTPException(status_code=404, detail="Insurance plan not found")

        # Get updated coverage details
        coverage_details = await provider_service.get_coverage_details(
            policy_number=insurance.policy_number,
            member_id=current_user.id
        )

        # Update coverage details
        await add_coverage_detail(
            db,
            InsuranceCoverageDetailCreate(
                insurance_plan_id=updated_plan.id,
                coverage_type="comprehensive",
                benefits=coverage_details.get("benefits"),
                exclusions=coverage_details.get("exclusions")
            )
        )

        await provider_service.close()
        return updated_plan

    except Exception as e:
        await provider_service.close()
        raise HTTPException(status_code=500, detail=str(e))

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

@router.post("/claims", response_model=MedicareClaimResponse)
async def submit_claim(
    claim: MedicareClaimCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Submit a new Medicare claim."""
    provider_service = InsuranceProviderService()
    
    try:
        # Get insurance plan
        result = await db.execute(
            select(InsurancePlan).filter(InsurancePlan.id == claim.insurance_plan_id)
        )
        insurance = result.scalars().first()
        
        if not insurance:
            raise HTTPException(status_code=404, detail="Insurance plan not found")

        # Submit claim to insurance provider
        claim_result = await provider_service.submit_claim(
            policy_number=insurance.policy_number,
            member_id=current_user.id,
            claim_data=claim.dict()
        )

        # Add claim to database
        claim_response = await add_medicare_claim(db, claim)

        await provider_service.close()
        return claim_response

    except Exception as e:
        await provider_service.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/wallet/export/{insurance_id}")
async def export_digital_wallet_card(
    insurance_id: int,
    wallet_type: str = "apple",  # or "google"
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Export a digital wallet-friendly JSON card for Apple/Google Wallet."""
    result = await db.execute(select(InsurancePlan).filter(InsurancePlan.id == insurance_id))
    insurance = result.scalars().first()
    if not insurance:
        raise HTTPException(status_code=404, detail="Insurance plan not found")

    wallet_service = DigitalWalletService()
    
    try:
        if wallet_type.lower() == "apple":
            card = await wallet_service.generate_apple_wallet_pass(
                "insurance",
                {
                    "id": insurance.id,
                    "name": current_user.full_name,
                    "policy_number": insurance.policy_number,
                    "provider": insurance.provider_name
                }
            )
        else:
            card = await wallet_service.generate_google_wallet_pass(
                "insurance",
                {
                    "id": insurance.id,
                    "name": current_user.full_name,
                    "policy_number": insurance.policy_number,
                    "provider": insurance.provider_name
                }
            )

        return JSONResponse(content=card)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))