from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.user import User
from app.schemas.user import UserCreate,UserUpdate
from app.core.security import hash_password  

async def create_user(db: AsyncSession, user: UserCreate):
    hashed_password = hash_password(user.password)  

    new_user = User(
        email=user.email,
        full_name=user.full_name,
        password_hash=hashed_password,  
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)  
    return new_user  

async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()

async def get_active_users(db: AsyncSession):
    """Retrieve all active users from the database."""
    result = await db.execute(select(User).filter(User.is_active == True))
    return result.scalars().all() 
 
async def get_users(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate):
    user = await get_user(db, user_id)
    if not user:
        return None  

    
    update_data = user_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(user, key, value)  

    await db.commit()
    await db.refresh(user)
    return user

async def delete_user(db: AsyncSession, user_id: int):
    user = await get_user(db, user_id)
    if user:
        await db.delete(user)
        await db.commit()
    return user
