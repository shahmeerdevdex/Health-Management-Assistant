from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from typing import List
from app.schemas.vaccination import VaccinationReminder
from app.schemas.vaccination import (
    VaccinationRecordRequest,
    VaccinationRecordResponse,
    VaccinationRemindersResponse,
    NationalImmunizationSyncResponse
)
from app.db.models.vaccination import VaccinationRecord
from utils.send_vaccination_reminder import send_vaccination_reminder
from datetime import datetime, timedelta

async def process_vaccination_record(request: VaccinationRecordRequest, db: Session) -> VaccinationRecordResponse:
    """
    Stores vaccination records in the database and schedules reminders.
    """
    try:
        record = VaccinationRecord(
            user_id=request.user_id,
            vaccine_name=request.vaccine_name,
            dose_number=request.dose_number,
            date_administered=request.date_administered,
            healthcare_provider=request.healthcare_provider,
            next_due_date=request.next_due_date,
            user_email=request.user_email,  # Added email
            user_phone=request.user_phone   # Added phone
        )

        db.add(record)
        await db.commit()
        await db.refresh(record)

        # Schedule reminder if next_due_date is set
        if record.next_due_date:
            await send_vaccination_reminder(request.user_email, request.user_phone, record.next_due_date, request.vaccine_name)

    except SQLAlchemyError as e:
        await db.rollback()
        raise Exception(f"Database error: {str(e)}")

    return VaccinationRecordResponse(
        record_id=record.id,
        user_id=request.user_id,
        vaccine_name=request.vaccine_name,
        dose_number=request.dose_number,
        date_administered=request.date_administered,
        healthcare_provider=request.healthcare_provider,
        next_due_date=request.next_due_date,
        user_email=record.user_email,  # Ensure it's returned
        user_phone=record.user_phone   # Ensure it's returned
    )

async def get_vaccination_record(record_id: int, db: Session) -> VaccinationRecordResponse:
    """Retrieve a specific vaccination record by ID."""
    record = await db.get(VaccinationRecord, record_id)
    if not record:
        return None
    return VaccinationRecordResponse(
        record_id=record.id,
        user_id=record.user_id,
        vaccine_name=record.vaccine_name,
        dose_number=record.dose_number,
        date_administered=record.date_administered,
        healthcare_provider=record.healthcare_provider,
        next_due_date=record.next_due_date,
        user_email=record.user_email,
        user_phone=record.user_phone
    )

async def update_vaccination_record(record_id: int, request: VaccinationRecordRequest, db: Session) -> VaccinationRecordResponse:
    """Update an existing vaccination record."""
    record = await db.get(VaccinationRecord, record_id)
    if not record:
        return None
    try:
        record.vaccine_name = request.vaccine_name
        record.dose_number = request.dose_number
        record.date_administered = request.date_administered
        record.healthcare_provider = request.healthcare_provider
        record.next_due_date = request.next_due_date
        record.user_email = request.user_email  # Ensure email is updated
        record.user_phone = request.user_phone  # Ensure phone is updated

        await db.commit()
        await db.refresh(record)

        # Reschedule reminder if next_due_date changes
        if record.next_due_date:
            await send_vaccination_reminder(request.user_email, request.user_phone, record.next_due_date, request.vaccine_name)

    except SQLAlchemyError as e:
        await db.rollback()
        raise Exception(f"Database error: {str(e)}")

    return VaccinationRecordResponse(
        record_id=record.id,
        user_id=record.user_id,
        vaccine_name=record.vaccine_name,
        dose_number=record.dose_number,
        date_administered=record.date_administered,
        healthcare_provider=request.healthcare_provider,
        next_due_date=record.next_due_date,
        user_email=record.user_email,  # Ensure it's returned
        user_phone=record.user_phone   # Ensure it's returned
    )

async def delete_vaccination_record(record_id: int, db: Session) -> bool:
    """Delete a vaccination record by ID."""
    record = await db.get(VaccinationRecord, record_id)
    if not record:
        return False
    try:
        await db.delete(record)
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        raise Exception(f"Database error: {str(e)}")

async def get_vaccination_reminders(user_id: int, db: Session) -> List[VaccinationReminder]:
    """
    Fetch upcoming vaccination reminders for a user.
    """
    today = datetime.utcnow()
    query = select(VaccinationRecord).where(
        VaccinationRecord.user_id == user_id,
        VaccinationRecord.next_due_date >= today
    )
    result = await db.execute(query)
    upcoming_vaccines = result.scalars().all()

    if not upcoming_vaccines:
        return []

    reminders = [
    VaccinationReminder(
        vaccine_name=rec.vaccine_name,
        next_due_date=rec.next_due_date,
        reminder_sent_at=datetime.utcnow(),
        healthcare_provider=rec.healthcare_provider
    )
    for rec in upcoming_vaccines
]

    return reminders

from datetime import datetime

async def sync_national_vaccine_records(user_id: int, db: Session):
    """
    Dummy function to simulate syncing with a national immunization system.
    """
    national_data = [
        {"vaccine_name": "COVID-19 Booster", "dose_number": 2, "date_administered": "2024-01-10"},
        {"vaccine_name": "Influenza", "dose_number": 1, "date_administered": "2023-11-15"},
    ]

    synced_records = []

    for record in national_data:
        # Check if record already exists
        existing_record = await db.execute(
            select(VaccinationRecord).where(
                VaccinationRecord.user_id == user_id,
                VaccinationRecord.vaccine_name == record["vaccine_name"],
                VaccinationRecord.dose_number == record["dose_number"]
            )
        )
        if existing_record.scalar():
            continue

        # Convert string to date
        administered_date = datetime.strptime(record["date_administered"], "%Y-%m-%d").date()

        new_record = VaccinationRecord(
            user_id=user_id,
            vaccine_name=record["vaccine_name"],
            dose_number=record["dose_number"],
            date_administered=administered_date,
            healthcare_provider="National Health Database",
            next_due_date=None
        )

        db.add(new_record)
        synced_records.append(new_record)

    await db.commit()
    
    return NationalImmunizationSyncResponse(
        user_id=user_id,
        synced_records=[
            VaccinationRecordResponse(
                record_id=record.id,
                user_id=record.user_id,
                vaccine_name=record.vaccine_name,
                dose_number=record.dose_number,
                date_administered=record.date_administered,
                healthcare_provider=record.healthcare_provider,
                next_due_date=record.next_due_date,
                user_email=record.user_email,
                user_phone=record.user_phone
            )
            for record in synced_records
        ]
    )

