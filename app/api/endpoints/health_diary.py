from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.health_diary import HealthDiaryCreate, HealthDiaryResponse,HealthDiaryUpdate
from app.crud.health_diary import create_health_diary, get_health_diary,update_health_diary
from app.api.endpoints.dependencies import get_current_user 

router = APIRouter()

@router.post("/add-entry", response_model=HealthDiaryResponse)
async def add_health_diary_entry(
    entry: HealthDiaryCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)  
):
    """
    Add a new health diary entry.

    This is a **protected endpoint** that requires authentication. 
    Users can log their health-related notes and symptoms.

    Args:
        entry (HealthDiaryCreate): The health diary entry details (e.g., symptoms, mood).
        db (AsyncSession): Database session dependency.
        current_user (User): The authenticated user.

    Returns:
        HealthDiaryResponse: The created health diary entry.
    """
    new_entry = await create_health_diary(db, entry) 
    return new_entry

@router.get("/{user_id}", response_model=list[HealthDiaryResponse])
async def get_health_diary_entries(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)  
):
    """
    Retrieve all health diary entries for a specific user.

    This is a **protected endpoint** that requires authentication.
    Users can fetch all their logged health diary entries.

    Args:
        user_id (int): The ID of the user whose health diary entries should be retrieved.
        db (AsyncSession): Database session dependency.
        current_user (User): The authenticated user.

    Returns:
        list[HealthDiaryResponse]: A list of health diary entries. If no entries exist, an empty list is returned.
    """
    entries = await get_health_diary(db, user_id)
    return entries if entries else []

@router.put("/update-entry/{entry_id}", response_model=HealthDiaryResponse)
async def update_health_diary_entry(
    entry_id: int,
    updated_entry: HealthDiaryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Update an existing health diary entry.

    This is a **protected endpoint** that requires authentication.
    Users can update their previously logged health diary notes or symptoms.

    Args:
        entry_id (int): ID of the health diary entry to update.
        updated_entry (HealthDiaryUpdate): Updated health diary entry data.
        db (AsyncSession): Database session dependency.
        current_user (User): The authenticated user.

    Returns:
        HealthDiaryResponse: The updated health diary entry.
    """
    updated = await update_health_diary(db, entry_id, updated_entry)
    if not updated:
        raise HTTPException(status_code=404, detail="Health diary entry not found or access denied")
    return updated
