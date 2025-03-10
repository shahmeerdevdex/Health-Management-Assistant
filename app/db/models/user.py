from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from app.db.models.roles import user_roles 

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    notifications = relationship("Notification", back_populates="user")
    health_diary_entries = relationship("HealthDiary", back_populates="user")
    medications = relationship("Medication", back_populates="user")  
    appointments = relationship("Appointment", back_populates="user", cascade="all, delete-orphan")
    telehealth_sessions = relationship("TelehealthSession", back_populates="user")

    
    roles = relationship("Role", secondary=user_roles, back_populates="users")
