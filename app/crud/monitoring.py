from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.monitoring import ChronicMonitoring
from datetime import datetime

async def get_chronic_monitoring(db: AsyncSession, user_id: int):
    """
    Retrieves chronic monitoring data for a user.
    """
    result = await db.execute(
        select(ChronicMonitoring)
        .filter(ChronicMonitoring.patient_id == user_id)
        .order_by(ChronicMonitoring.recorded_at.desc())
    )
    return result.scalars().first() 