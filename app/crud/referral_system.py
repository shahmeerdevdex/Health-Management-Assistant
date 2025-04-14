from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from app.db.models.referral_system import Referral
from app.schemas.referral_system import ReferralCreate, ReferralUpdate
from datetime import datetime


async def create_referral(db: AsyncSession, referral: ReferralCreate) -> Referral:
    new_referral = Referral(
        patient_id=referral.patient_id,
        from_practitioner_id=referral.from_practitioner_id,
        to_practitioner_id=referral.to_practitioner_id,
        reason=referral.reason,
        notes=referral.notes,
        status="PENDING",
        created_at=datetime.utcnow()
    )
    db.add(new_referral)
    await db.commit()
    await db.refresh(new_referral)
    return new_referral


async def get_referral(db: AsyncSession, referral_id: int) -> Referral | None:
    result = await db.execute(select(Referral).where(Referral.id == referral_id))
    return result.scalars().first()


async def get_referrals_for_practitioner(db: AsyncSession, practitioner_id: int) -> list[Referral]:
    result = await db.execute(
        select(Referral).where(
            (Referral.from_practitioner_id == practitioner_id) |
            (Referral.to_practitioner_id == practitioner_id)
        )
    )
    return result.scalars().all()


async def update_referral(
    db: AsyncSession, referral_id: int, update_data: ReferralUpdate
) -> Referral | None:
    referral = await get_referral(db, referral_id)
    if not referral:
        return None

    if update_data.status:
        referral.status = update_data.status
    if update_data.notes is not None:
        referral.notes = update_data.notes

    await db.commit()
    await db.refresh(referral)
    return referral


async def delete_referral(db: AsyncSession, referral_id: int) -> bool:
    referral = await get_referral(db, referral_id)
    if not referral:
        return False
    await db.delete(referral)
    await db.commit()
    return True
