from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.telehealth import TelehealthSession
from app.schemas.telehealth import TelehealthSessionCreate

async def create_telehealth_session(db: AsyncSession, session_data: TelehealthSessionCreate):
    """
    Create a new telehealth session.
    """
    db_session = TelehealthSession(**session_data.dict())
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session

async def get_active_sessions(db: AsyncSession, user_id: int):
    """
    Retrieve active telehealth sessions for a user.
    """
    result = await db.execute(select(TelehealthSession).where(TelehealthSession.user_id == user_id, TelehealthSession.session_status == "active"))
    return result.scalars().all()
