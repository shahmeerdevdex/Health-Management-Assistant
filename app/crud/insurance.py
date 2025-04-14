from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.insurance import InsurancePlan
from app.schemas.insurance import InsuranceCreate, InsuranceResponse
from datetime import datetime
from enum import Enum

class VerificationStatusEnum(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value = value.upper()
            if value in cls.__members__:
                return cls[value]
        return super()._missing_(value)

async def add_insurance_plan(db: AsyncSession, user_id: int, insurance_data: InsuranceCreate):
    """Add a new insurance plan for a user."""
    new_plan = InsurancePlan(
        user_id=user_id,
        provider_name=insurance_data.provider_name,
        policy_number=insurance_data.policy_number,
        coverage_start=insurance_data.coverage_start,
        coverage_end=insurance_data.coverage_end,
        deductible=insurance_data.deductible,
        premium_amount=insurance_data.premium_amount
    )

    db.add(new_plan)
    await db.commit()
    await db.refresh(new_plan)

    return InsuranceResponse(
        id=new_plan.id,
        user_id=new_plan.user_id,
        provider_name=new_plan.provider_name,
        policy_number=new_plan.policy_number,
        coverage_start=new_plan.coverage_start,
        coverage_end=new_plan.coverage_end,
        deductible=new_plan.deductible,
        premium_amount=new_plan.premium_amount,
        is_verified=new_plan.is_verified,
        verification_status=new_plan.verification_status,
        verified_at=new_plan.verified_at,
    )

async def get_insurance_plans(db: AsyncSession, user_id: int):
    """Retrieve insurance plans for a user."""
    result = await db.execute(select(InsurancePlan).filter(InsurancePlan.user_id == user_id))
    return result.scalars().all()

async def update_insurance_plan(db: AsyncSession, insurance_id: int, insurance_data: InsuranceCreate):
    """Update an insurance plan."""
    result = await db.execute(select(InsurancePlan).filter(InsurancePlan.id == insurance_id))
    insurance = result.scalars().first()

    if not insurance:
        return None

    insurance.provider_name = insurance_data.provider_name
    insurance.policy_number = insurance_data.policy_number
    insurance.coverage_start = insurance_data.coverage_start
    insurance.coverage_end = insurance_data.coverage_end
    insurance.deductible = insurance_data.deductible
    insurance.premium_amount = insurance_data.premium_amount

    await db.commit()
    await db.refresh(insurance)
    return InsuranceResponse(
        id=insurance.id,
        user_id=insurance.user_id,
        provider_name=insurance.provider_name,
        policy_number=insurance.policy_number,
        coverage_start=insurance.coverage_start,
        coverage_end=insurance.coverage_end,
        deductible=insurance.deductible,
        premium_amount=insurance.premium_amount,
        is_verified=insurance.is_verified,
        verification_status=insurance.verification_status,
        verified_at=insurance.verified_at,
    )

async def delete_insurance_plan(db: AsyncSession, insurance_id: int):
    """Delete an insurance plan by ID."""
    result = await db.execute(select(InsurancePlan).filter(InsurancePlan.id == insurance_id))
    insurance = result.scalars().first()

    if insurance:
        await db.delete(insurance)
        await db.commit()
    return insurance


#  Simulation + Enum-based logic, ready to replace with Vericred
async def verify_insurance_coverage(
    insurance: InsurancePlan,
    first_name: str = "John",  # Simulated or replace with real
    last_name: str = "Doe",
    birth_date: str = "1990-01-01"
) -> dict:
    """
    Simulate third-party verification.
    Replace this block with Vericred integration in production.
    """
    last_char = insurance.policy_number[-1]
    approved = last_char.isdigit() and int(last_char) % 2 == 0

    return {
        "is_verified": approved,
        "verification_status": VerificationStatusEnum.VERIFIED if approved else VerificationStatusEnum.REJECTED,
        "verified_at": datetime.utcnow() if approved else None
    }


async def apply_insurance_verification_logic(
    db: AsyncSession, insurance_id: int
) -> InsurancePlan | None:
    """
    Apply verification logic (simulated for now, Vericred-ready).
    """
    result = await db.execute(select(InsurancePlan).filter(InsurancePlan.id == insurance_id))
    insurance = result.scalars().first()

    if not insurance:
        return None

    # Simulated logic — pass user data when integrating real Vericred API
    verification_data = await verify_insurance_coverage(
        insurance,
        first_name="Ali",  # TODO: pull from user table if needed
        last_name="Khan",
        birth_date="1990-01-01"
    )

    insurance.is_verified = verification_data["is_verified"]
    insurance.verification_status = verification_data["verification_status"]
    insurance.verified_at = verification_data["verified_at"]

    await db.commit()
    await db.refresh(insurance)
    return insurance
