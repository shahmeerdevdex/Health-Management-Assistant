from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # e.g., "premium_family"
    description = Column(String, nullable=True)
    price_usd = Column(Float, nullable=False)
    stripe_price_id_usd = Column(String, nullable=True)
    features = Column(JSON, nullable=True)  # {"max_ai_uses": 10, "report_access": True}
    is_active = Column(Boolean, default=True)

    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    stripe_subscription_id = Column(String, unique=True, nullable=True)
    
    status = Column(String, default="active")  # e.g., active, past_due, canceled, incomplete
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)

    users = relationship("User", back_populates="subscription")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
