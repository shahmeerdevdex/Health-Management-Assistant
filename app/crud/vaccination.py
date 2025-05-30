from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.vaccination import VaccinationRecord
from datetime import datetime

async def get_vaccination_records(db: AsyncSession, user_id: int):
    """
    Retrieves vaccination records for a user.
    """
    result = await db.execute(
        select(VaccinationRecord)
        .filter(VaccinationRecord.user_id == user_id)
        .order_by(VaccinationRecord.date_administered.desc())
    )
    return result.scalars().all() 