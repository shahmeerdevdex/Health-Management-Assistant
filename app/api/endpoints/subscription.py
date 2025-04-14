from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api.endpoints.dependencies import get_db, get_current_user
from app.crud.subscription import (
    get_all_subscription_plans,
    create_subscription_plan,
    get_subscription_plan,
    get_user_subscription,
    change_user_subscription
)
from app.schemas.subscription import SubscriptionPlanCreate, SubscriptionPlanResponse, SubscriptionResponse
from app.db.models.user import UserRoleEnum  

router = APIRouter()


@router.post("/", response_model=SubscriptionPlanResponse, response_model_exclude_none=True)
async def create_plan(
    plan: SubscriptionPlanCreate, 
    db: AsyncSession = Depends(get_db),
    db_user=Depends(get_current_user)
):
    """Create a new subscription plan (admin only)."""
    if db_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create subscription plans")
    
    try:
        new_plan = await create_subscription_plan(db, plan)
        return new_plan
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to create plan")


@router.get("/", response_model=List[SubscriptionPlanResponse])
async def list_subscription_plans(
    db: AsyncSession = Depends(get_db),
    db_user=Depends(get_current_user)
):
    """List all available subscription plans."""
    return await get_all_subscription_plans(db)


@router.get("/status", response_model=SubscriptionResponse)
async def get_my_subscription(
    db: AsyncSession = Depends(get_db),
    db_user=Depends(get_current_user)
):
    """Check current user's subscription and status."""
    subscription = await get_user_subscription(db, db_user.id)
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found for user")
    return subscription


@router.post("/change", response_model=SubscriptionResponse)
async def change_my_subscription(
    new_plan_id: int,
    db: AsyncSession = Depends(get_db),
    db_user=Depends(get_current_user)
):
    """Change or upgrade the current user's subscription plan."""
    plan = await get_subscription_plan(db, new_plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(status_code=404, detail="Selected plan does not exist or is inactive")

    try:
        subscription = await change_user_subscription(db, user_id=db_user.id, new_plan=plan)
        return subscription
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to change subscription: {str(e)}")
