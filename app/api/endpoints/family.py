from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from sqlalchemy.future import select    
from app.api.endpoints.dependencies import get_db, get_current_user
from app.db.models.user import User, UserRoleInput
from app.db.models.family import FamilyLink, FamilyHealthSummary
from app.services.family_health_service import FamilyHealthService
from app.schemas.family import (
    FamilyLinkCreate,
    FamilyLinkResponse,
    FamilyHealthSummaryResponse,
    FamilyMemberResponse
)

router = APIRouter()

@router.post("/links", response_model=FamilyLinkResponse)
async def create_family_link(
    link_data: FamilyLinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new family link between users."""
    # Verify user has permission to create family links
    if current_user.role not in [UserRoleInput.PRIMARY_HOLDER, UserRoleInput.FAMILY_MEMBER]:
        raise HTTPException(
            status_code=403,
            detail="Only primary holders and family members can create family links"
        )

    # Create family link
    family_link = FamilyLink(
        user_id=current_user.id,
        family_member_id=link_data.family_member_id,
        relationship_type=link_data.relationship_type,
        sharing_preferences=link_data.sharing_preferences
    )
    
    db.add(family_link)
    await db.commit()
    await db.refresh(family_link)
    
    return family_link

@router.get("/health-summary/{family_link_id}", response_model=FamilyHealthSummaryResponse)
async def get_family_health_summary(
    family_link_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive health summary for a family unit."""
    # Verify user has access to this family link
    family_link = await db.execute(
        select(FamilyLink).where(
            (FamilyLink.id == family_link_id) &
            ((FamilyLink.user_id == current_user.id) | (FamilyLink.family_member_id == current_user.id))
        )
    )
    family_link = family_link.scalar_one_or_none()
    
    if not family_link:
        raise HTTPException(
            status_code=404,
            detail="Family link not found or access denied"
        )

    # Generate or get existing summary
    family_service = FamilyHealthService(db)
    try:
        summary = await family_service.generate_family_health_summary(family_link_id)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating family health summary: {str(e)}"
        )

@router.get("/members", response_model=List[FamilyMemberResponse])
async def get_family_members(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all family members for the current user."""
    # Get all family links where user is either the primary or the member
    family_links = await db.execute(
        select(FamilyLink).where(
            (FamilyLink.user_id == current_user.id) |
            (FamilyLink.family_member_id == current_user.id)
        )
    )
    family_links = family_links.scalars().all()
    
    members = []
    for link in family_links:
        # Get the other user in the relationship
        other_user_id = link.family_member_id if link.user_id == current_user.id else link.user_id
        other_user = await db.execute(
            select(User).where(User.id == other_user_id)
        )
        other_user = other_user.scalar_one_or_none()
        
        if other_user:
            members.append({
                "user_id": other_user.id,
                "name": other_user.full_name,
                "relationship_type": link.relationship_type,
                "sharing_preferences": link.sharing_preferences
            })
    
    return members
