from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm  
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import authenticate_user, create_access_token
from app.core.config import settings
from app.db.session import get_db
from app.crud.user import create_user
from app.api.endpoints.dependencies import get_db
from app.db.models.user import User
from sqlalchemy.future import select 
from app.schemas.user import UserCreate, UserResponse 
import logging


router = APIRouter()

@router.post("/registration/create", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user with basic information.
    Required fields:
    - email
    - full_name
    - password
    - role (optional, defaults to FAMILY_MEMBER)
    """
    try:
        new_user = await create_user(db=db, user=user)
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": new_user.email},
            expires_delta=access_token_expires
        )
        
        # Return user data matching UserResponse model
        return UserResponse(
            email=new_user.email,
            full_name=new_user.full_name,
            is_active=new_user.is_active,
            created_at=new_user.created_at,
            role=new_user.role,
            subscription_id=new_user.subscription_id,
            stripe_customer_id=new_user.stripe_customer_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the user: {str(e)}"
        )

logger = logging.getLogger("auth")
#  Existing JSON-based login for API calls
@router.post("/login", response_model=TokenResponse,summary="Login")
async def login_json(request: Request, login_data: LoginRequest, db: AsyncSession = Depends(get_db)): 
    """
    Handles user authentication by validating credentials and issuing an access token (JSON request).

    Args:
        login_data (LoginRequest): The login request containing user email and password.
        db (AsyncSession): The database session dependency.

    Returns:
        dict: A dictionary containing the access token and token type.

    Raises:
        HTTPException: If the provided credentials are invalid.
    """

    logger.info(f"Login attempt from IP: {request.client.host}")

    if not login_data.email or not login_data.password:
        raise HTTPException(status_code=422, detail="Both email and password are required.")

    user = await authenticate_user(db, login_data.email, login_data.password)

    if not user:
        logger.warning(f"Failed login attempt for email: {login_data.email}")
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = await create_access_token(user.id, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    
    logger.info(f"User {user.id} authenticated successfully.")

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token", response_model=TokenResponse,include_in_schema=False)
async def login_oauth2(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)): 
    """
    Handles user authentication using OAuth2PasswordRequestForm (for Swagger UI login).

    Args:
        form_data (OAuth2PasswordRequestForm): The form data containing username (email) and password.
        db (AsyncSession): The database session dependency.

    Returns:
        dict: A dictionary containing the access token and token type.

    Raises:
        HTTPException: If the provided credentials are invalid.
    """
    email = form_data.username

    user = await authenticate_user(db, email, form_data.password)

    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = await create_access_token(user.id, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    
    return {"access_token": access_token, "token_type": "bearer"}