from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy.future import select
from app.db.models.user import User, UserRoleInput
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
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

from app.db.models.family import FamilyLink  #Required for family linking

async def create_user(db: AsyncSession, user: UserCreate):
    """Create a new user with proper error handling and validations."""
    try:
        # Check if email already exists
        result = await db.execute(select(User).where(User.email == user.email))
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail=f"Email '{user.email}' is already registered."
            )

        # Run password hashing in threadpool
        hashed_password = await run_in_threadpool(hash_password, user.password)

        # Validate role
        try:
            role_enum = UserRoleInput(user.role.upper())
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid role '{user.role}'. Allowed values: {[r.value for r in UserRoleInput]}"
            )

        # Create Stripe customer
        try:
            stripe_customer = await run_in_threadpool(
                stripe.Customer.create,
                email=user.email,
                name=user.full_name,
                metadata={"app_user_role": user.role}
            )
        except Exception:
            logger.error("Stripe error:\n" + traceback.format_exc())
            raise HTTPException(status_code=502, detail="Stripe customer creation failed.")

        # Set default date_of_birth if none provided, ensuring it's date only
        if user.date_of_birth:
            # Convert to date only by taking just the date part
            date_of_birth = user.date_of_birth.date()
        else:
            date_of_birth = datetime(2000, 1, 1).date()

        # Build user object
        new_user = User(
            email=user.email,
            full_name=user.full_name,
            password_hash=hashed_password,
            is_active=True,
            role=role_enum,
            stripe_customer_id=stripe_customer.id,
            date_of_birth=date_of_birth
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Create FamilyLink if primary_holder_id is provided
        if user.primary_holder_id:
            # Validate primary_holder_id exists and is of role PRIMARY_HOLDER
            result = await db.execute(select(User).where(User.id == user.primary_holder_id))
            primary_holder = result.scalar_one_or_none()

            if not primary_holder:
                raise HTTPException(status_code=404, detail="Primary holder user not found.")

            if primary_holder.role != UserRoleInput.PRIMARY_HOLDER:
                raise HTTPException(status_code=403, detail="Only users with role 'PRIMARY_HOLDER' can be assigned as family heads.")

            family_link = FamilyLink(
                user_id=primary_holder.id,
                family_member_id=new_user.id,
                relationship_type=user.relationship_type or "dependent",
                sharing_preferences=user.sharing_preferences or {
                    "share_medical": True,
                    "share_activity": False
                }
            )
            db.add(family_link)
            await db.commit()

        return new_user

    except IntegrityError:
        await db.rollback()
        logger.error("DB integrity error:\n" + traceback.format_exc())
        raise HTTPException(status_code=409, detail="User could not be created due to duplicate or invalid data.")

    except HTTPException:
        raise

    except Exception:
        await db.rollback()
        logger.error("Unexpected error during user creation:\n" + traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error while creating user.")

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
            role_enum = UserRoleInput(update_data["role"]) if isinstance(update_data["role"], str) else update_data["role"]
            if user.role == UserRoleInput.FAMILY_MEMBER:
                update_data.pop("role")
            else:
                update_data["role"] = role_enum
        except ValueError:
            raise ValueError(f"Invalid role '{update_data['role']}'. Allowed values: {[r.value for r in UserRoleInput]}")

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
