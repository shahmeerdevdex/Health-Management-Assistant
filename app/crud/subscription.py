from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, and_
from app.db.models.subscription import SubscriptionPlan, Subscription
from app.schemas.subscription import (
    SubscriptionPlanCreate,
    SubscriptionUpdate,
    SubscriptionCancel,
    SubscriptionStatus
)
from app.core.config import settings
import stripe
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger("main")


def get_default_features(plan_name: str) -> dict:
    name = plan_name.lower()
    if "freemium" in name:
        return {
            "ai_insights": False,
            "max_health_entries": 10,
            "max_users": 1,
            "telehealth": False,
            "ehr_access": False
        }
    elif "premium" in name:
        return {
            "ai_insights": True,
            "max_health_entries": 100,
            "max_users": 5,
            "telehealth": True,
            "ehr_access": False
        }
    elif "provider" in name:
        return {
            "ai_insights": True,
            "max_health_entries": -1,  # Unlimited
            "max_users": 20,
            "telehealth": True,
            "ehr_access": True,
            "analytics": True
        }
    elif "enterprise" in name:
        return {
            "ai_insights": True,
            "max_health_entries": -1,
            "max_users": -1,
            "telehealth": True,
            "ehr_access": True,
            "analytics": True,
            "custom_branding": True,
            "population_health": True
        }
    return {}


async def create_subscription_plan(db: AsyncSession, plan_data: SubscriptionPlanCreate) -> SubscriptionPlan:
    data = plan_data.dict()

    if data["price_usd"] > 0:
        product = stripe.Product.create(
            name=data["name"],
            description=data["description"]
        )
        price = stripe.Price.create(
            unit_amount=int(data["price_usd"] * 100),
            currency="usd",
            recurring={"interval": data["billing_cycle"]},
            product=product.id
        )
        data["stripe_price_id_usd"] = price.id
    else:
        data["stripe_price_id_usd"] = None

    if not data.get("features"):
        data["features"] = get_default_features(data["name"])

    db_plan = SubscriptionPlan(**data)
    db.add(db_plan)
    await db.commit()
    await db.refresh(db_plan)
    return db_plan


async def get_subscription_plan(db: AsyncSession, plan_id: int) -> Optional[SubscriptionPlan]:
    result = await db.execute(select(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id))
    return result.scalars().first()


async def get_all_subscription_plans(db: AsyncSession):
    result = await db.execute(select(SubscriptionPlan).filter(SubscriptionPlan.is_active == True))
    return result.scalars().all()


async def create_user_subscription(
    db: AsyncSession,
    user_id: int,
    plan: SubscriptionPlan,
    payment_method_id: Optional[str] = None
) -> Subscription:
    try:
        # Create or get Stripe customer
        customer = stripe.Customer.create(
            metadata={"user_id": user_id}
        )

        # Create subscription
        subscription_data = {
            "customer": customer.id,
            "items": [{"price": plan.stripe_price_id_usd}],
        }

        if payment_method_id:
            subscription_data["default_payment_method"] = payment_method_id

        if plan.trial_period_days:
            subscription_data["trial_period_days"] = plan.trial_period_days

        stripe_subscription = stripe.Subscription.create(**subscription_data)

        # Create database record
        db_sub = Subscription(
            user_id=user_id,
            plan_id=plan.id,
            stripe_subscription_id=stripe_subscription.id,
            status=SubscriptionStatus(stripe_subscription.status),
            start_date=datetime.fromtimestamp(stripe_subscription.start_date),
            current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
            current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
            trial_end=datetime.fromtimestamp(stripe_subscription.trial_end) if stripe_subscription.trial_end else None,
            cancel_at_period_end=stripe_subscription.cancel_at_period_end,
            payment_method_id=payment_method_id
        )
        
        db.add(db_sub)
        await db.commit()
        await db.refresh(db_sub)
        return db_sub
    except Exception as e:
        logger.error(f"Failed to create subscription: {str(e)}")
        raise


async def update_subscription(
    db: AsyncSession,
    user_id: int,
    update_data: SubscriptionUpdate
) -> Subscription:
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    subscription = result.scalars().first()
    
    if not subscription:
        raise ValueError("No subscription found for user")

    try:
        stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
        
        if update_data.billing_cycle:
            # Update billing cycle
            new_price = stripe.Price.create(
                unit_amount=int(subscription.plan.price_usd * 100),
                currency="usd",
                recurring={"interval": update_data.billing_cycle},
                product=stripe_sub.items.data[0].price.product
            )
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    'id': stripe_sub.items.data[0].id,
                    'price': new_price.id,
                }],
                proration_behavior='always_invoice'
            )
            subscription.billing_cycle_anchor = datetime.utcnow()

        if update_data.payment_method_id:
            # Update payment method
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                default_payment_method=update_data.payment_method_id
            )
            subscription.payment_method_id = update_data.payment_method_id

        if update_data.cancel_at_period_end is not None:
            # Update cancellation status
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=update_data.cancel_at_period_end
            )
            subscription.cancel_at_period_end = update_data.cancel_at_period_end

        await db.commit()
        await db.refresh(subscription)
        return subscription
    except Exception as e:
        logger.error(f"Failed to update subscription: {str(e)}")
        raise


async def cancel_subscription(
    db: AsyncSession,
    user_id: int,
    cancel_data: SubscriptionCancel
) -> Subscription:
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    subscription = result.scalars().first()
    
    if not subscription:
        raise ValueError("No subscription found for user")

    try:
        if cancel_data.cancel_at_period_end:
            # Cancel at period end
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
            subscription.cancel_at_period_end = True
        else:
            # Cancel immediately
            stripe.Subscription.delete(subscription.stripe_subscription_id)
            subscription.status = SubscriptionStatus.CANCELED
            subscription.end_date = datetime.utcnow()

        await db.commit()
        await db.refresh(subscription)
        return subscription
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {str(e)}")
        raise


async def get_subscription_usage(db: AsyncSession, user_id: int) -> Dict[str, Any]:
    """Get subscription usage statistics."""
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    subscription = result.scalars().first()
    
    if not subscription:
        raise ValueError("No subscription found for user")

    # Get plan features
    plan = await get_subscription_plan(db, subscription.plan_id)
    if not plan:
        raise ValueError("Subscription plan not found")

    # Calculate usage statistics
    usage = {
        "plan_name": plan.name,
        "status": subscription.status,
        "current_period": {
            "start": subscription.current_period_start,
            "end": subscription.current_period_end
        },
        "features": {}
    }

    # Add feature usage statistics
    for feature, limit in plan.features.items():
        if isinstance(limit, (int, float)):
            # Get actual usage for this feature
            # This is a placeholder - implement actual usage tracking for each feature
            usage["features"][feature] = {
                "limit": limit,
                "used": 0,  # Implement actual usage tracking
                "remaining": limit
            }

    return usage


async def update_subscription_status(
    db: AsyncSession,
    stripe_subscription_id: str,
    new_status: str
) -> None:
    """Update subscription status from Stripe webhook."""
    await db.execute(
        update(Subscription)
        .where(Subscription.stripe_subscription_id == stripe_subscription_id)
        .values(
            status=SubscriptionStatus(new_status),
            last_payment_status=new_status,
            last_payment_date=datetime.utcnow()
        )
    )
    await db.commit()


async def save_sub_plan_to_db(
    db: AsyncSession,
    name: str,
    description: str,
    stripe_product_id: str,
    stripe_price_id: str,
    amount: int,
    currency: str
):
    existing = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.stripe_price_id_usd == stripe_price_id)
    )
    plan = existing.scalars().first()

    if plan:
        plan.name = name
        plan.description = description
        plan.price_usd = amount / 100
        logger.info(f"Updated existing subscription plan: {name} ({stripe_price_id})")
    else:
        features = get_default_features(name)

        new_plan = SubscriptionPlan(
            name=name,
            description=description,
            stripe_price_id_usd=stripe_price_id,
            price_usd=amount / 100,
            features=features,
            is_active=True
        )
        db.add(new_plan)
        logger.info(f"Created new subscription plan: {name} ({stripe_price_id}) with default features")

    await db.commit()


async def get_user_subscription_status(db: AsyncSession, user_id: int) -> dict:
    """
    Fetch user's subscription status and plan details for dashboard display.
    """
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    sub = result.scalars().first()

    if not sub:
        return {"status": "inactive", "plan": "Freemium"}

    plan = await get_subscription_plan(db, sub.plan_id)

    return {
        "status": sub.status,
        "plan": plan.name if plan else "Unknown",
        "features": plan.features if plan and plan.features else {}
    }


async def get_user_subscription(db: AsyncSession, user_id: int) -> Optional[Subscription]:
    """Get a user's subscription details."""
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    return result.scalars().first()


async def change_user_subscription(
    db: AsyncSession,
    user_id: int,
    new_plan_id: int,
    payment_method_id: Optional[str] = None
) -> Subscription:
    """Change a user's subscription to a different plan."""
    # Get current subscription
    current_sub = await get_user_subscription(db, user_id)
    if not current_sub:
        raise ValueError("No active subscription found for user")

    # Get new plan
    new_plan = await get_subscription_plan(db, new_plan_id)
    if not new_plan:
        raise ValueError("New subscription plan not found")

    try:
        # Get Stripe subscription
        stripe_sub = stripe.Subscription.retrieve(current_sub.stripe_subscription_id)

        # Create new price for the plan
        new_price = stripe.Price.create(
            unit_amount=int(new_plan.price_usd * 100),
            currency="usd",
            recurring={"interval": current_sub.billing_cycle or "month"},
            product=stripe_sub.items.data[0].price.product
        )

        # Update subscription with new price
        updated_sub = stripe.Subscription.modify(
            current_sub.stripe_subscription_id,
            items=[{
                'id': stripe_sub.items.data[0].id,
                'price': new_price.id,
            }],
            proration_behavior='always_invoice'
        )

        # Update payment method if provided
        if payment_method_id:
            stripe.Subscription.modify(
                current_sub.stripe_subscription_id,
                default_payment_method=payment_method_id
            )
            current_sub.payment_method_id = payment_method_id

        # Update database record
        current_sub.plan_id = new_plan_id
        current_sub.current_period_start = datetime.fromtimestamp(updated_sub.current_period_start)
        current_sub.current_period_end = datetime.fromtimestamp(updated_sub.current_period_end)
        
        await db.commit()
        await db.refresh(current_sub)
        return current_sub

    except Exception as e:
        logger.error(f"Failed to change subscription: {str(e)}")
        raise
