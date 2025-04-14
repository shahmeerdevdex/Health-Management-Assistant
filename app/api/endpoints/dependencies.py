from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from jose import JWTError, ExpiredSignatureError
from app.db.session import get_db
from app.services.auth_service import verify_access_token
from app.db.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: str = Security(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    """Retrieve the current authenticated user from the database using async SQLAlchemy."""
    try:
        payload = await verify_access_token(token)
        user_id = payload.get("user_id")

        if not user_id or not isinstance(user_id, int):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Add selectinload for relationships you need (e.g., practitioner_relationships)
    result = await db.execute(
        select(User)
        .options(selectinload(User.practitioner_relationships))  
        .where(User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
