from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.medication import Medication
from app.schemas.medication import MedicationCreate, MedicationUpdate
from datetime import datetime, timezone

async def create_medication(db: AsyncSession, med: MedicationCreate):
    medication = Medication(
        user_id=med.user_id,  
        name=med.name,
        dosage=med.dosage,
        frequency=med.frequency,
        start_date=med.start_date.replace(tzinfo=None) if med.start_date.tzinfo else med.start_date,
        end_date=med.end_date.replace(tzinfo=None) if med.end_date and med.end_date.tzinfo else med.end_date
    )
    db.add(medication)
    await db.commit()
    await db.refresh(medication)
    return medication

async def get_medication(db: AsyncSession, med_id: int):
    result = await db.execute(select(Medication).filter(Medication.id == med_id))
    return result.scalars().first()

async def get_medications(db: AsyncSession, user_id: int):
    result = await db.execute(select(Medication).filter(Medication.user_id == user_id))
    return result.scalars().all()

async def delete_medication(db: AsyncSession, med_id: int):
    medication = await get_medication(db, med_id)
    if medication:
        await db.delete(medication)
        await db.commit()
        return {"message": "Medication deleted successfully"}  
    return {"error": "Medication not found"}  

async def update_medication(db: AsyncSession, med_id: int, med_update: MedicationUpdate):
    result = await db.execute(select(Medication).filter(Medication.id == med_id))
    medication = result.scalars().first()

    if not medication:
        return {"error": "Medication not found"}  
    if med_update.name is not None:
        medication.name = med_update.name
    if med_update.dosage is not None:
        medication.dosage = med_update.dosage
    if med_update.frequency is not None:
        medication.frequency = med_update.frequency
    if med_update.start_date is not None:
        medication.start_date = med_update.start_date.replace(tzinfo=None) if med_update.start_date.tzinfo else med_update.start_date
    if med_update.end_date is not None:
        medication.end_date = med_update.end_date.replace(tzinfo=None) if med_update.end_date.tzinfo else med_update.end_date

    await db.commit()
    await db.refresh(medication)
    
    return medication 