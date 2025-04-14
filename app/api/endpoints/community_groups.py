from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.community import SupportGroupCreate, SupportGroupResponse, GroupPostCreate
from app.db.models.community import SupportGroup, CommunityPost
from app.db.session import get_db
from app.api.endpoints.dependencies import get_current_user

router = APIRouter()


@router.get("/support-groups", response_model=list[SupportGroupResponse])
async def list_support_groups(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SupportGroup))
    return result.scalars().all()


@router.get("/support-groups/{group_id}", response_model=SupportGroupResponse)
async def get_group(group_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SupportGroup).where(SupportGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Support group not found")
    return group


@router.post("/support-groups", response_model=SupportGroupResponse)
async def create_support_group(group: SupportGroupCreate, db: AsyncSession = Depends(get_db)):
    new_group = SupportGroup(**group.dict())
    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)
    return new_group


@router.get("/community/groups/{group_id}/posts")
async def list_group_posts(group_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CommunityPost).where(CommunityPost.group_id == group_id).order_by(CommunityPost.created_at.desc())
    )
    return result.scalars().all()


@router.post("/community/groups/{group_id}/post")
async def create_group_post(
    group_id: int,
    post: GroupPostCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    new_post = CommunityPost(
        user_id=current_user.id,
        group_id=group_id,
        title=post.title,
        content=post.content,
        is_anonymous=post.is_anonymous,
        category="group"  # Can still be used for filtering
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return {"id": new_post.id, "message": "Post created in group"}
