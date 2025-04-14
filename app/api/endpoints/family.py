from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.family import FamilyLinkCreate, FamilyLinkResponse
from app.crud.family_links import (
    create_family_link,
    get_users_linked_to_me,
    get_family_links_for_user
)
from app.api.endpoints.dependencies import get_current_user

router = APIRouter()


@router.post("/family-link", response_model=FamilyLinkResponse)
async def link_family_member(
    payload: FamilyLinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Link a family member to the current user."""
    link = await create_family_link(
        db=db,
        user_id=current_user.id,
        family_member_id=payload.family_member_id,
        relation_type=payload.relation_type,
        permission=payload.permission
    )
    if not link:
        raise HTTPException(status_code=400, detail="Link already exists.")
    return link


@router.get("/family-linked-users", response_model=list[FamilyLinkResponse])
async def get_linked_users(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Fetch all users who have shared access with the current user."""
    return await get_users_linked_to_me(db=db, family_member_id=current_user.id)


@router.get("/family-members", response_model=list[FamilyLinkResponse])
async def get_my_family_members(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Fetch all family members the current user has linked."""
    return await get_family_links_for_user(db=db, user_id=current_user.id)
