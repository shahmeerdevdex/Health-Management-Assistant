from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.health_diary import HealthDiary
from app.db.models.user import User  # Import User model to validate user existence
from app.schemas.health_diary import HealthDiaryCreate, HealthDiaryUpdate
from datetime import datetime

async def create_health_diary(db: AsyncSession, diary: HealthDiaryCreate):
    # Check if the user exists
    user_check = await db.execute(select(User).filter(User.id == diary.user_id))
    user = user_check.scalars().first()
    if not user:
        raise ValueError(f"User with ID {diary.user_id} does not exist")

    # Ensure date is naive (no timezone issues)
    diary_date = diary.date
    if diary_date.tzinfo is not None:
        diary_date = diary_date.astimezone().replace(tzinfo=None)

    new_entry = HealthDiary(
        user_id=diary.user_id,
        date=diary_date,
        symptoms=diary.symptoms,  # Ensure symptoms field is included
        mood=diary.mood,
        notes=diary.notes
    )
    db.add(new_entry)
    await db.commit()
    await db.refresh(new_entry)
    return new_entry

async def get_health_diary(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 10):
    result = await db.execute(select(HealthDiary).filter(HealthDiary.user_id == user_id).offset(skip).limit(limit))
    entries = result.scalars().all()
    return entries if entries else [] 

async def get_health_diaries(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 10):
    result = await db.execute(select(HealthDiary).filter(HealthDiary.user_id == user_id).offset(skip).limit(limit))
    return result.scalars().all()

async def delete_health_diary(db: AsyncSession, entry_id: int):
    entry = await get_health_diary(db, entry_id)
    if entry:
        await db.delete(entry)
        await db.commit()
    return entry

async def update_health_diary(db: AsyncSession, entry_id: int, diary_update: HealthDiaryUpdate):
    result = await db.execute(select(HealthDiary).filter(HealthDiary.id == entry_id))
    entry = result.scalars().first()

    if not entry:
        return None 
    
    if diary_update.symptoms is not None:
        entry.symptoms = diary_update.symptoms
    if diary_update.mood is not None:
        entry.mood = diary_update.mood
    if diary_update.notes is not None:
        entry.notes = diary_update.notes

    await db.commit()
    await db.refresh(entry)
    return entry
