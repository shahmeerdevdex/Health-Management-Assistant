from fastapi import HTTPException
from .subscription_tiers import SUBSCRIPTION_TIERS
from sqlalchemy.orm import Session
from app.crud.subscription import get_user_subscription

def has_feature_access(db: Session, user_id: int, feature: str) -> bool:
    """Check if a user has access to a specific feature based on their subscription plan."""
    subscription = get_user_subscription(db, user_id)

    if not subscription:
        raise HTTPException(status_code=403, detail="No active subscription found.")

    plan_name = subscription.plan  # e.g., "freemium", "premium_family"
    allowed_features = SUBSCRIPTION_TIERS.get(plan_name, {}).get("features", [])

    return feature in allowed_features
