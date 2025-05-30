from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class PharmacyOrder(Base):
    __tablename__ = "pharmacy_orders"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    medications = Column(JSON, nullable=False)  # List of medications ordered
    delivery_address = Column(String, nullable=False)
    payment_method = Column(String, default="card")
    insurance_used = Column(Boolean, default=False)
    status = Column(String, default="Processing")  # Possible statuses: Processing, Shipped, Delivered
    estimated_delivery = Column(DateTime, nullable=True)
    order_date = Column(DateTime, default=datetime.utcnow)
    stripe_payment_intent_id = Column(String, nullable=True)
    
    user = relationship("User", back_populates="pharmacy_orders")
