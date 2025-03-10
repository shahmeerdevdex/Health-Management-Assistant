from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm  
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import authenticate_user, create_access_token
from app.core.config import settings
from app.db.session import get_db
import logging

router = APIRouter()

# Setup logging
logger = logging.getLogger("auth")


#  Existing JSON-based login for API calls
@router.post("/login", response_model=TokenResponse)
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


#  New OAuth2-based login for Swagger UI (expects username instead of email)
@router.post("/token", response_model=TokenResponse)
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

    user = await authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = await create_access_token(user.id, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    
    return {"access_token": access_token, "token_type": "bearer"}