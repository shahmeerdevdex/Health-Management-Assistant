from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.crud.user import create_user, get_user, update_user
from app.db.models.user import User
from app.services.auth_service import verify_access_token  

router = APIRouter()

@router.post("/users/create", response_model=UserResponse)
async def create_user_endpoint(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.

    This is a public endpoint that allows new users to create an account.

    Args:
        user (UserCreate): The user registration details including email, full name, and password.
        db (AsyncSession): Database session dependency.

    Returns:
        UserResponse: The newly created user object.
    """
    new_user = await create_user(db, user)  
    return new_user

@router.get("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(verify_access_token)])
async def get_user_endpoint(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve user details by ID.

    This is a protected endpoint that requires authentication. Users can fetch details 
    of a specific user by providing the `user_id`.

    Args:
        user_id (int): The ID of the user to fetch.
        db (AsyncSession): Database session dependency.

    Returns:
        UserResponse: The user details.

    Raises:
        HTTPException (404): If the user is not found.
    """
    result = await db.execute(select(User).where(User.id == user_id))  
    user = result.scalars().first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user 

@router.put("/users/update/{user_id}", response_model=UserResponse, dependencies=[Depends(verify_access_token)])
async def update_user_endpoint(user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_db)):
    """
    Update an existing user's details.

    This is a protected endpoint that requires authentication. 
    Users can update their information such as email or full name.

    Args:
        user_id (int): The ID of the user to update.
        user_update (UserUpdate): The updated user details.
        db (AsyncSession): Database session dependency.

    Returns:
        UserResponse: The updated user object.

    Raises:
        HTTPException (404): If the user is not found.
    """
    updated_user = await update_user(db, user_id, user_update)  

    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return updated_user
