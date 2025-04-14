from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.endpoints.dependencies import get_db, get_current_user
from app.schemas.roles import RoleUpdateRequest, RoleResponse
from app.db.models.user import User, UserRoleEnum

router = APIRouter()

@router.get("/roles", response_model=RoleResponse)
async def get_user_role(
    db: AsyncSession = Depends(get_db),
    db_user = Depends(get_current_user)  
):
    """
    Retrieves the current role of the logged-in user.
    """
    return {"user_id": db_user.id, "role": db_user.role}

@router.put("/roles", response_model=RoleResponse)
async def update_user_role(
    request: RoleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    db_user = Depends(get_current_user)
):
    """
    Updates the user's role (Only Primary Account Holder can update roles).
    """
    if db_user.role != UserRoleEnum.PRIMARY_HOLDER:
        raise HTTPException(status_code=403, detail="Only Primary Account Holders can update roles")

    result = await db.execute(select(User).filter(User.id == request.user_id))
    user_to_update = result.scalars().first()

    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")

    user_to_update.role = request.new_role
    await db.commit()
    await db.refresh(user_to_update)
    
    return {"user_id": user_to_update.id, "role": user_to_update.role}
