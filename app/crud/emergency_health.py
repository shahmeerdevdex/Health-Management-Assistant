from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.emergency_health_ids import EmergencyHealthID
from app.schemas.emergency_health_ids import EmergencyHealthIDCreate, EmergencyHealthIDResponse

async def create_or_update_emergency_health(db: AsyncSession, user_id: int, health_data: EmergencyHealthIDCreate):
    """
    Creates or updates Emergency Health ID for a user.
    """
    result = await db.execute(select(EmergencyHealthID).filter(EmergencyHealthID.user_id == user_id))
    existing_health_id = result.scalars().first()

    if existing_health_id:
        # Update existing record
        existing_health_id.allergies = health_data.allergies
        existing_health_id.medications = health_data.medications
        existing_health_id.emergency_contact_name = health_data.emergency_contact_name
        existing_health_id.emergency_contact_phone = health_data.emergency_contact_phone
        existing_health_id.critical_conditions = health_data.critical_conditions
        await db.commit()
        await db.refresh(existing_health_id)
        return existing_health_id

    # Create new record
    new_health_id = EmergencyHealthID(user_id=user_id, **health_data.dict())
    db.add(new_health_id)
    await db.commit()
    await db.refresh(new_health_id)

    return new_health_id

async def get_emergency_health_id(db: AsyncSession, user_id: int):
    """
    Retrieves Emergency Health ID for a given user.
    """
    result = await db.execute(select(EmergencyHealthID).filter(EmergencyHealthID.user_id == user_id))
    return result.scalars().first()
