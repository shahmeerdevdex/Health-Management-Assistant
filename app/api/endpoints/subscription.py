from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api.endpoints.dependencies import get_db, get_current_user
from app.crud.subscription import (
    get_all_subscription_plans,
    create_subscription_plan,
    get_subscription_plan,
    get_user_subscription,
    change_user_subscription,
    update_subscription_status,
    cancel_subscription,
    update_subscription,
    get_subscription_usage as get_usage_stats
)
from app.schemas.subscription import (
    SubscriptionPlanCreate,
    SubscriptionPlanResponse,
    SubscriptionResponse,
    SubscriptionUpdate,
    SubscriptionCancel
)
from app.db.models.user import UserRoleInput
from app.services.payment_service import create_stripe_checkout
from app.core.config import settings
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/", response_model=SubscriptionPlanResponse)
async def create_plan(
    plan: SubscriptionPlanCreate, 
    db: AsyncSession = Depends(get_db),
    db_user=Depends(get_current_user)
):
    """Create a new subscription plan (admin only)."""
    if db_user.role != UserRoleInput.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create subscription plans")
    
    try:
        new_plan = await create_subscription_plan(db, plan)
        return new_plan
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create plan: {str(e)}")

@router.get("/plans", response_model=List[SubscriptionPlanResponse])
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
    """Get current user's subscription status with detailed information."""
    subscription = await get_user_subscription(db, db_user.id)
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found for user")
    
    # Calculate days until renewal and trial days remaining
    if subscription.current_period_end:
        days_until_renewal = (subscription.current_period_end - datetime.utcnow()).days
        subscription.days_until_renewal = max(0, days_until_renewal)
    
    if subscription.trial_end:
        trial_days_remaining = (subscription.trial_end - datetime.utcnow()).days
        subscription.trial_days_remaining = max(0, trial_days_remaining)
    
    # Check if upgrade/downgrade is possible
    if subscription.plan:
        subscription.can_upgrade = bool(subscription.plan.upgrade_path)
        subscription.can_downgrade = bool(subscription.plan.downgrade_path)
    
    return subscription

@router.post("/subscribe/{plan_id}")
async def subscribe_to_plan(
    plan_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    db_user=Depends(get_current_user)
):
    """Subscribe to a new plan or upgrade/downgrade existing subscription."""
    plan = await get_subscription_plan(db, plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(status_code=404, detail="Selected plan does not exist or is inactive")

    try:
        # Create Stripe checkout session
        success_url = f"{settings.FRONTEND_URL}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{settings.FRONTEND_URL}/subscription/cancel"
        
        checkout_url = create_stripe_checkout(
            price_id=plan.stripe_price_id_usd,
            quantity=1,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        return {"checkout_url": checkout_url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create subscription: {str(e)}")

@router.put("/update", response_model=SubscriptionResponse)
async def update_my_subscription(
    update_data: SubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
    db_user=Depends(get_current_user)
):
    """Update subscription settings (billing cycle, payment method, etc.)."""
    try:
        updated_sub = await update_subscription(db, db_user.id, update_data)
        return updated_sub
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update subscription: {str(e)}")

@router.post("/cancel", response_model=SubscriptionResponse)
async def cancel_my_subscription(
    cancel_data: SubscriptionCancel,
    db: AsyncSession = Depends(get_db),
    db_user=Depends(get_current_user)
):
    """Cancel subscription (immediately or at period end)."""
    try:
        cancelled_sub = await cancel_subscription(db, db_user.id, cancel_data)
        return cancelled_sub
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to cancel subscription: {str(e)}")

@router.get("/usage")
async def get_subscription_usage(
    db: AsyncSession = Depends(get_db),
    db_user=Depends(get_current_user)
):
    """Get current subscription usage statistics."""
    try:
        usage_stats = await get_usage_stats(db, db_user.id)
        return usage_stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get usage statistics: {str(e)}")
