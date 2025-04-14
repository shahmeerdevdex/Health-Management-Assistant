from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy.future import select
from app.db.models.user import User, UserRoleEnum
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password  
from app.core.config import settings
import stripe
from app.db.models.practitioners import Practitioner
from app.db.models.caregiver import Caregiver
from fastapi.concurrency import run_in_threadpool
from app.db.models.mental_health import Professional


# Set Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY

from app.db.models.practitioners import Practitioner  

async def create_user(db: AsyncSession, user: UserCreate):
    """Create a new user and register practitioner or caregiver if applicable."""

    # Fix 1: Run password hashing in threadpool
    hashed_password = await run_in_threadpool(hash_password, user.password)

    # Fix 2: Validate role
    try:
        role_enum = UserRoleEnum(user.role.upper())
    except ValueError:
        raise ValueError(f"Invalid role '{user.role}'. Allowed values: {[r.value for r in UserRoleEnum]}")

    # Fix 3: Run Stripe (sync lib) in threadpool
    stripe_customer = await run_in_threadpool(
        stripe.Customer.create,
        email=user.email,
        name=user.full_name,
        metadata={"app_user_role": user.role}
    )

    # Create user
    new_user = User(
        email=user.email,
        full_name=user.full_name,
        password_hash=hashed_password,
        is_active=True,
        role=role_enum,
        subscription_id=user.subscription_id,
        stripe_customer_id=stripe_customer.id
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # If practitioner
    if role_enum == UserRoleEnum.PRACTITIONER:
        if not user.specialty or not user.contact_info:
            raise ValueError("Practitioner must include specialty and contact_info")

        new_practitioner = Practitioner(
            name=new_user.full_name,
            specialty=user.specialty,
            contact_info=user.contact_info,
            user_id=new_user.id
        )
        db.add(new_practitioner)
        await db.commit()
        await db.refresh(new_user)
        await db.refresh(new_practitioner)

    # If caregiver
    elif role_enum == UserRoleEnum.CAREGIVER:
        new_caregiver = Caregiver(
            user_id=new_user.id,
            name=new_user.full_name,
            phone=user.phone
        )
        db.add(new_caregiver)
        await db.commit()
        await db.refresh(new_caregiver)
        
    # If user is a professional, create a Professional entry
    elif role_enum == UserRoleEnum.PROFESSIONAL:
     if not user.specialty or not user.contact_info or not user.location:
        raise ValueError("Professional must include specialty, contact_info, and location")

    new_professional = Professional(
        user_id=new_user.id,
        name=new_user.full_name,
        specialty=user.specialty,
        contact_info=user.contact_info,
        location=user.location,
        accepts_insurance=user.accepts_insurance,
        online_available=user.online_available
    )
    db.add(new_professional)
    await db.commit()
    await db.refresh(new_professional)    

    return new_user


async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()


async def get_active_users(db: AsyncSession):
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

    # Ensure role updates are restricted
    if "role" in update_data:
        try:
            role_enum = UserRoleEnum(update_data["role"]) if isinstance(update_data["role"], str) else update_data["role"]
            if user.role == UserRoleEnum.FAMILY_MEMBER:
                update_data.pop("role")
            else:
                update_data["role"] = role_enum
        except ValueError:
            raise ValueError(f"Invalid role '{update_data['role']}'. Allowed values: {[r.value for r in UserRoleEnum]}")

    # Handle subscription updates
    if "subscription_id" in update_data:
        user.subscription_id = update_data["subscription_id"]

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
