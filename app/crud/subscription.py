from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from app.db.models.subscription import SubscriptionPlan, Subscription
from app.schemas.subscription import SubscriptionPlanCreate
from app.core.config import settings
import stripe
import logging
from datetime import datetime

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger("main")


def get_default_features(plan_name: str) -> dict:
    name = plan_name.lower()
    if "freemium" in name:
        return {"ai_insights": False, "max_health_entries": 10}
    elif "premium" in name:
        return {"ai_insights": True, "max_health_entries": 100}
    elif "provider" in name:
        return {"ehr_access": True, "telehealth": True}
    elif "enterprise" in name:
        return {
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
            recurring={"interval": "month"},
            product=product.id
        )
        data["stripe_price_id_usd"] = price.id
    else:
        data["stripe_price_id_usd"] = None

    # Add default features if none provided
    if not data.get("features"):
        data["features"] = get_default_features(data["name"])

    db_plan = SubscriptionPlan(**data)
    db.add(db_plan)
    await db.commit()
    await db.refresh(db_plan)
    return db_plan


async def get_subscription_plan(db: AsyncSession, plan_id: int):
    result = await db.execute(select(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id))
    return result.scalars().first()


async def get_all_subscription_plans(db: AsyncSession):
    result = await db.execute(select(SubscriptionPlan).filter(SubscriptionPlan.is_active == True))
    return result.scalars().all()


async def create_user_subscription(db: AsyncSession, user_id: int, plan: SubscriptionPlan) -> Subscription:
    stripe_subscription = stripe.Subscription.create(
        customer=user_id,  # Assuming this is the Stripe customer ID
        items=[{"price": plan.stripe_price_id_usd}]
    )

    db_sub = Subscription(
        user_id=user_id,
        plan_id=plan.id,
        stripe_subscription_id=stripe_subscription.id,
        status=stripe_subscription.status,
        start_date=datetime.utcnow()
    )
    db.add(db_sub)
    await db.commit()
    await db.refresh(db_sub)
    return db_sub


async def change_user_subscription(db: AsyncSession, user_id: int, new_plan: SubscriptionPlan):
    result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    current_sub = result.scalars().first()

    if current_sub:
        try:
            stripe.Subscription.delete(current_sub.stripe_subscription_id)
        except Exception as e:
            logger.warning(f"Stripe cancellation failed for user {user_id}: {e}")

        await db.delete(current_sub)
        await db.commit()

    return await create_user_subscription(db, user_id, new_plan)


async def get_user_subscription(db: AsyncSession, user_id: int) -> Subscription:
    result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    return result.scalars().first()


async def update_subscription_status(db: AsyncSession, stripe_subscription_id: str, new_status: str):
    await db.execute(
        update(Subscription)
        .where(Subscription.stripe_subscription_id == stripe_subscription_id)
        .values(status=new_status)
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
