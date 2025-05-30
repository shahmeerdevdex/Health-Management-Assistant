from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class HealthCheckIn(Base):
    __tablename__ = "health_checkins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    check_in_time = Column(DateTime(timezone=True), default=datetime.utcnow)  
    health_metrics = Column(JSON, nullable=False)
    risk_score = Column(Float, nullable=True)
    requires_attention = Column(Boolean, default=False)
    attention_reason = Column(String, nullable=True)
    notification_sent = Column(Boolean, default=False)
    notification_time = Column(DateTime(timezone=True), nullable=True)  

    user = relationship("User", back_populates="health_checkins")

class HealthCheckInSchedule(Base):
    __tablename__ = "health_checkin_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    frequency = Column(String, nullable=False)
    preferred_time = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    last_check_in = Column(DateTime(timezone=True), nullable=True) 
    next_check_in = Column(DateTime(timezone=True), nullable=True)  
    reminder_preferences = Column(JSON, nullable=True)

    user = relationship("User", back_populates="checkin_schedule")
