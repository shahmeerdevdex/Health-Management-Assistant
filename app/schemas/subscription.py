from pydantic import BaseModel, Field
from typing import Optional, Dict,List,Union
from datetime import datetime



class SubscriptionPlanBase(BaseModel):
    name: str
    description: str
    price_usd: float
    stripe_price_id_usd: Optional[str] = None
    features: Optional[Dict[str, Union[str, int, float, bool]]] = Field(default_factory=dict)
    is_active: bool = True
    is_active: bool = True


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
    status: Optional[str] = "active"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionResponse(SubscriptionBase):
    id: int
    plan: Optional[SubscriptionPlanResponse] = None 

    class Config:
        from_attributes = True
