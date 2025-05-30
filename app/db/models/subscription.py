from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from app.schemas.subscription import SubscriptionStatus, BillingCycle

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # e.g., "premium_family"
    description = Column(String, nullable=True)
    price_usd = Column(Float, nullable=False)
    stripe_price_id_usd = Column(String, nullable=True)
    features = Column(JSON, nullable=True)  # {"max_ai_uses": 10, "report_access": True}
    is_active = Column(Boolean, default=True)
    billing_cycle = Column(Enum(BillingCycle), default=BillingCycle.MONTHLY)
    trial_period_days = Column(Integer, nullable=True)
    max_users = Column(Integer, nullable=True)
    upgrade_path = Column(JSON, nullable=True)  # List of plan IDs
    downgrade_path = Column(JSON, nullable=True)  # List of plan IDs

    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    stripe_subscription_id = Column(String, unique=True, nullable=True)
    
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.INCOMPLETE)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    billing_cycle_anchor = Column(DateTime, nullable=True)
    last_payment_status = Column(String, nullable=True)
    last_payment_date = Column(DateTime, nullable=True)
    next_payment_date = Column(DateTime, nullable=True)
    payment_method_id = Column(String, nullable=True)

    users = relationship("User", back_populates="subscription")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
