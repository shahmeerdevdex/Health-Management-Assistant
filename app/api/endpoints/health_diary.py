from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.health_diary import HealthDiaryCreate, HealthDiaryResponse
from app.crud.health_diary import create_health_diary, get_health_diary
from app.services.auth_service import verify_access_token  
router = APIRouter()

@router.post("/health-diary/add-entry", response_model=HealthDiaryResponse, dependencies=[Depends(verify_access_token)])
async def add_health_diary_entry(entry: HealthDiaryCreate, db: AsyncSession = Depends(get_db)):
    """
    Add a new health diary entry.

    This is a **protected endpoint** that requires authentication. 
    Users can log their health-related notes and symptoms.

    Args:
        entry (HealthDiaryCreate): The health diary entry details (e.g., symptoms, mood).
        db (AsyncSession): Database session dependency.

    Returns:
        HealthDiaryResponse: The created health diary entry.

    Raises:
        HTTPException (400): If there is an issue creating the entry.
    """
    new_entry = await create_health_diary(db, entry) 
    return new_entry

@router.get("/health-diary/{user_id}", response_model=list[HealthDiaryResponse], dependencies=[Depends(verify_access_token)])
async def get_health_diary_entries(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve all health diary entries for a specific user.

    This is a **protected endpoint** that requires authentication.
    Users can fetch all their logged health diary entries.

    Args:
        user_id (int): The ID of the user whose health diary entries should be retrieved.
        db (AsyncSession): Database session dependency.

    Returns:
        list[HealthDiaryResponse]: A list of health diary entries. If no entries exist, an empty list is returned.
    """
    entries = await get_health_diary(db, user_id)
    return entries if entries else []
