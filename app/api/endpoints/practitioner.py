from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.practitioner import PractitionerCreate, PractitionerResponse, PatientSummary
from app.schemas.referral_system import ReferralCreate, ReferralResponse, ReferralUpdate
from app.crud.practitioner import create_practitioner, get_practitioners
from app.crud.referral_system import create_referral, get_referral , get_referrals_for_practitioner, update_referral
from app.api.endpoints.dependencies import get_current_user
from app.db.models.user import UserRoleEnum
from typing import List
from app.db.models.user import User
from app.db.models.health_diary import HealthDiary
from app.db.models.medication import Medication
from app.crud.analytics import get_provider_analytics
from app.schemas.messaging import MessageCreate, MessageResponse
from app.crud.messaging import create_message, get_messages_between_users

router = APIRouter()

@router.post("/add", response_model=PractitionerResponse)
async def add_practitioner_endpoint(
    practitioner: PractitionerCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != UserRoleEnum.PRIMARY_HOLDER:
        raise HTTPException(status_code=403, detail="Only Primary Account Holders can add practitioners.")

    return await create_practitioner(db, practitioner)

@router.get("/list", response_model=List[PractitionerResponse])
async def list_practitioners(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    practitioners = await get_practitioners(db)
    return practitioners

@router.get("/dashboard", response_model=List[PatientSummary])
async def practitioner_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != UserRoleEnum.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can access the dashboard.")

    await db.refresh(current_user)
    if not current_user.practitioner_profile:
        raise HTTPException(status_code=404, detail="Practitioner profile not found")

    practitioner = current_user.practitioner_profile
    patients = practitioner.patients

    summaries = []

    for patient in patients:
        diary_entry = None
        if patient.health_diary_entries:
            latest_entry = sorted(patient.health_diary_entries, key=lambda e: e.created_at, reverse=True)[0]
            diary_entry = latest_entry.entry_text

        meds = [med.name for med in patient.medications if med.is_active]
        alerts = []

        summaries.append(PatientSummary(
            id=patient.id,
            full_name=patient.full_name,
            email=patient.email,
            latest_diary_entry=diary_entry,
            active_medications=meds,
            alerts=alerts
        ))

    return summaries

@router.get("/analytics/overview")
async def practitioner_analytics_overview(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != UserRoleEnum.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can access analytics.")

    await db.refresh(current_user, attribute_names=["practitioner_profile"])
    if not current_user.practitioner_profile:
      raise HTTPException(status_code=404, detail="Practitioner profile not found")

    return await get_provider_analytics(db=db, practitioner_id=current_user.practitioner_profile.id)


@router.post("/referrals/send", response_model=ReferralResponse)
async def send_referral(
    referral: ReferralCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != UserRoleEnum.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can send referrals.")

    if referral.from_practitioner_id == referral.to_practitioner_id:
        raise HTTPException(status_code=400, detail="Cannot refer to yourself.")

    return await create_referral(db=db, referral=referral)

@router.get("/referrals/my", response_model=List[ReferralResponse])
async def view_referrals(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != UserRoleEnum.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can view referrals.")

    await db.refresh(current_user, attribute_names=["practitioner_profile"])
    if not current_user.practitioner_profile:
      raise HTTPException(status_code=404, detail="Practitioner profile not found")

    return await get_referrals_for_practitioner(db=db, practitioner_id=current_user.practitioner_profile.id)

@router.put("/referrals/update/{referral_id}", response_model=ReferralResponse)
async def update_referral_endpoint(
    referral_id: int,
    referral_update: ReferralUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != UserRoleEnum.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can update referrals.")

    return await update_referral(db=db, referral_id=referral_id, update_data=referral_update)

# Secure Messaging
@router.post("/send", response_model=MessageResponse)
async def send_message(
    message: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await create_message(
        db=db,
        sender_id=current_user.id,
        receiver_id=message.receiver_id,
        message_data=message
    )

@router.get("/chat/{receiver_id}", response_model=List[MessageResponse])
async def get_chat_messages(
    receiver_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await get_messages_between_users(db=db, peer_id=current_user.id, user_id=receiver_id)