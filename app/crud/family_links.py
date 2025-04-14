from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.family import FamilyLink


async def create_family_link(
    db: AsyncSession,
    user_id: int,
    family_member_id: int,
    relation_type: str,
    permission: str = "read"
):
    """Create a family sharing link between two users."""
    existing_link = await db.execute(
        select(FamilyLink).where(
            FamilyLink.user_id == user_id,
            FamilyLink.family_member_id == family_member_id
        )
    )
    if existing_link.scalar_one_or_none():
        return None  # Link already exists

    new_link = FamilyLink(
        user_id=user_id,
        family_member_id=family_member_id,
        relation_type=relation_type,
        permission=permission
    )
    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)
    return new_link


async def get_family_links_for_user(db: AsyncSession, user_id: int):
    """Get all family members linked by this user."""
    result = await db.execute(
        select(FamilyLink).where(FamilyLink.user_id == user_id)
    )
    return result.scalars().all()


async def get_users_linked_to_me(db: AsyncSession, family_member_id: int):
    """Get all users who have shared access with the current user."""
    result = await db.execute(
        select(FamilyLink).where(FamilyLink.family_member_id == family_member_id)
    )
    return result.scalars().all()


async def is_family_authorized(db: AsyncSession, user_id: int, current_user_id: int):
    """Check if current_user_id has access to user_id's data."""
    if user_id == current_user_id:
        return True  # Owner access

    result = await db.execute(
        select(FamilyLink).where(
            FamilyLink.user_id == user_id,
            FamilyLink.family_member_id == current_user_id
        )
    )
    return result.scalar_one_or_none() is not None
