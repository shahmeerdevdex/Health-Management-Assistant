from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer  #  For Swagger UI authentication
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.config import settings
from app.core.security import verify_password
from app.db.models.user import User

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

#  This allows FastAPI to read the token from "Authorization: Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")  

async def authenticate_user(db: AsyncSession, email: str, password: str):
    """Authenticate a user by verifying the email and password."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()  

    if not user or not verify_password(password, user.password_hash):  
        return None
    return user

async def create_access_token(user_id: int, expires_delta: timedelta = None):
    """Generate a JWT access token for a user."""
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_access_token(token: str = Depends(oauth2_scheme)):
    """Verify and decode a JWT access token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception

        return {"user_id": int(user_id), "expires": payload["exp"]}

    except JWTError:
        raise credentials_exception
