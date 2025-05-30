from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.config import settings
from app.core.security import verify_password
from app.db.models.user import User
from app.db.models.oauth_token import UserOAuthToken

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Remove duplicate oauth2_scheme declaration, use the one from dependencies.py

async def authenticate_user(db: AsyncSession, email: str, password: str):
    """Authenticate a user by verifying the email and password."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()  

    if not user or not verify_password(password, user.password_hash):  
        return None
    return user

async def create_access_token(data: dict = None, user_id: int = None, expires_delta: timedelta = None):
    """Support both explicit user_id and generic data dict."""
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    if data:
        to_encode = {**data, "exp": expire}
    elif user_id:
        to_encode = {"user_id": user_id, "exp": expire}
    else:
        raise ValueError("Either 'user_id' or 'data' must be provided.")

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def verify_access_token(token: str):
    """Verify and decode a JWT access token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")  # Now looking for "user_id" instead of "sub"
        if not user_id:
            raise credentials_exception

        return {"user_id": int(user_id), "expires": payload["exp"]}

    except JWTError:
        raise credentials_exception
    
    
async def get_user_oauth_token(db: AsyncSession, user_id: int, provider: str) -> UserOAuthToken | None:
    """Get an existing OAuth token for a given user and provider."""
    result = await db.execute(
        select(UserOAuthToken).where(
            UserOAuthToken.user_id == user_id,
            UserOAuthToken.provider == provider
        )
    )
    return result.scalars().first()

async def save_or_update_oauth_token(
    db: AsyncSession,
    user_id: int,
    provider: str,
    access_token: str,
    refresh_token: str = None,
    expires_at: datetime = None
) -> UserOAuthToken:
    """Save or update an OAuth token for a user/provider pair."""
    token = await get_user_oauth_token(db, user_id, provider)

    if token:
        token.access_token = access_token
        token.refresh_token = refresh_token
        token.expires_at = expires_at
    else:
        token = UserOAuthToken(
            user_id=user_id,
            provider=provider,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )
        db.add(token)

    await db.commit()
    await db.refresh(token)
    return token    