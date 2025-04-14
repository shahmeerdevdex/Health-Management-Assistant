from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from app.db.models.ehr_sync import EHRRecord  
from app.schemas.ehr_sync import EHRSyncRequest

async def get_ehr_record_by_user_id(db: AsyncSession, user_id: int) -> EHRRecord | None:
    result = await db.execute(select(EHRRecord).where(EHRRecord.user_id == user_id))
    return result.scalars().first()

async def upsert_ehr_record(db: AsyncSession, data: EHRSyncRequest) -> EHRRecord:
    record = await get_ehr_record_by_user_id(db, user_id=data.user_id)

    formatted_history = [
        {
            "condition": entry.condition,
            "diagnosed_on": entry.diagnosed_on.isoformat() 
        }
        for entry in data.medical_history
    ]

    if record:
        record.medical_history = formatted_history
        record.last_synced = datetime.utcnow()
    else:
        record = EHRRecord(
            user_id=data.user_id,
            medical_history=formatted_history,
            last_synced=datetime.utcnow()
        )
        db.add(record)

    await db.commit()
    await db.refresh(record)
    return record
