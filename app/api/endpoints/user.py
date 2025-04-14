from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.crud.user import create_user, update_user,delete_user
from app.db.models.user import User
from app.api.endpoints.dependencies import get_current_user
from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = APIRouter()

@router.post("/create", response_model=UserResponse)
async def create_user_endpoint(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.
    """
    new_user = await create_user(db, user)

    # Refresh the user from the DB with all fields eagerly loaded
    result = await db.execute(
        select(User).where(User.id == new_user.id)
    )
    loaded_user = result.scalars().first()

    return loaded_user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_endpoint(
    user_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Retrieve user details by ID.
    """
    result = await db.execute(select(User).where(User.id == user_id))  
    user = result.scalars().first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user 

@router.put("/update/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: int, 
    user_update: UserUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Update an existing user's details.
    """
    updated_user = await update_user(db, user_id, user_update)  

    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return updated_user

@router.delete("/delete/{user_id}")
async def delete_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Delete a user by ID.

    This is a **protected endpoint** that requires authentication.
    Only the authenticated user can delete their own account (or an admin with proper permissions).

    Args:
        user_id (int): ID of the user to be deleted.
        db (AsyncSession): Database session.
        current_user (User): The currently authenticated user.

    Returns:
        dict: Confirmation message upon successful deletion.
    """
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Operation not permitted")

    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"detail": "User deleted successfully"}