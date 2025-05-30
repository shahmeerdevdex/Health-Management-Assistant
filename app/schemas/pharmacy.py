from pydantic import BaseModel
from typing import List, Optional

class PharmacyOrderRequest(BaseModel):
    user_id: int  # The user placing the order
    medications: List[str]  # List of medications being ordered
    delivery_address: str  # Delivery address for the order
    payment_method: Optional[str] = "card"  # Payment method (default: card)
    insurance_used: Optional[bool] = False  # Whether insurance is applied
    stripe_payment_intent_id: Optional[str] = None
    total_amount: float

class PharmacyOrderResponse(BaseModel):
    order_id: int  # Unique ID for the order
    user_id: int
    medications: List[str]
    status: str  # Order status (e.g., "Processing", "Shipped", "Delivered")
    estimated_delivery: Optional[str]  # Estimated delivery date