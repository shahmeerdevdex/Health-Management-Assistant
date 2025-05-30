from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.orm import selectinload
from app.db.models.referral import Referral
from app.schemas.referral_system import ReferralCreate, ReferralUpdate
from datetime import datetime, timezone
from app.db.models.practitioners import Practitioner


async def create_referral(db: AsyncSession, referral: ReferralCreate) -> Referral:
    new_referral = Referral(
        patient_id=referral.patient_id,
        from_practitioner_id=referral.from_practitioner_id,
        to_practitioner_id=referral.to_practitioner_id,
        specialist_type=referral.specialist_type,
        reason=referral.reason,
        priority=referral.priority,
        notes=referral.notes,
        status="PENDING",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        appointment_date=None,
        feedback=None,
        medical_history_required=referral.medical_history_required,
        test_results_required=referral.test_results_required
    )
    db.add(new_referral)
    await db.commit()
    await db.refresh(new_referral)
    return new_referral


async def get_referral(db: AsyncSession, referral_id: int) -> Referral | None:
    result = await db.execute(select(Referral).where(Referral.id == referral_id))
    return result.scalars().first()


async def get_referrals_for_practitioner(db: AsyncSession, practitioner_id: int) -> list[Referral]:
    # First get the practitioner's user ID
    result = await db.execute(
        select(Practitioner).where(Practitioner.id == practitioner_id)
    )
    practitioner = result.scalar_one_or_none()
    if not practitioner:
        return []
    
    # Then query referrals using the user ID, with documents eagerly loaded
    result = await db.execute(
        select(Referral)
        .options(selectinload(Referral.documents))
        .where(
            (Referral.from_practitioner_id == practitioner.user_id) |
            (Referral.to_practitioner_id == practitioner.user_id)
        )
    )
    return result.scalars().all()


async def update_referral(
    db: AsyncSession, referral_id: int, update_data: ReferralUpdate
) -> Referral | None:
    # Get referral with documents eagerly loaded
    result = await db.execute(
        select(Referral)
        .options(selectinload(Referral.documents))
        .where(Referral.id == referral_id)
    )
    referral = result.scalar_one_or_none()
    if not referral:
        return None

    if update_data.status:
        referral.status = update_data.status
    if update_data.notes is not None:
        referral.notes = update_data.notes
    if update_data.feedback is not None:
        referral.feedback = update_data.feedback
    if update_data.appointment_date is not None:
        # Convert to UTC if timezone-aware, then remove timezone info
        if update_data.appointment_date.tzinfo is not None:
            utc_time = update_data.appointment_date.astimezone(timezone.utc)
            referral.appointment_date = utc_time.replace(tzinfo=None)
        else:
            referral.appointment_date = update_data.appointment_date

    # Set updated_at to UTC time without timezone info
    referral.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

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
