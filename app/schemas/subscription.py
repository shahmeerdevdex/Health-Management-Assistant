from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Union
from datetime import datetime
from enum import Enum

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    UNPAID = "unpaid"

class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    QUARTERLY = "quarterly"

class SubscriptionPlanBase(BaseModel):
    name: str
    description: str
    price_usd: float
    stripe_price_id_usd: Optional[str] = None
    features: Optional[Dict[str, Union[str, int, float, bool]]] = Field(default_factory=dict)
    is_active: bool = True
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    trial_period_days: Optional[int] = None
    max_users: Optional[int] = None
    upgrade_path: Optional[List[int]] = None  # List of plan IDs that this plan can upgrade to
    downgrade_path: Optional[List[int]] = None  # List of plan IDs that this plan can downgrade to

class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass

class SubscriptionPlanResponse(SubscriptionPlanBase):
    id: int

    class Config:
        from_attributes = True

class SubscriptionBase(BaseModel):
    user_id: int
    plan_id: int
    stripe_subscription_id: Optional[str] = None
    status: SubscriptionStatus = SubscriptionStatus.INCOMPLETE
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    billing_cycle_anchor: Optional[datetime] = None
    last_payment_status: Optional[str] = None
    last_payment_date: Optional[datetime] = None
    next_payment_date: Optional[datetime] = None
    payment_method_id: Optional[str] = None

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionResponse(SubscriptionBase):
    id: int
    plan: Optional[SubscriptionPlanResponse] = None
    can_upgrade: bool = False
    can_downgrade: bool = False
    days_until_renewal: Optional[int] = None
    trial_days_remaining: Optional[int] = None

    class Config:
        from_attributes = True

class SubscriptionUpdate(BaseModel):
    cancel_at_period_end: Optional[bool] = None
    payment_method_id: Optional[str] = None
    billing_cycle: Optional[BillingCycle] = None

class SubscriptionCancel(BaseModel):
    cancel_at_period_end: bool = True
    reason: Optional[str] = None
