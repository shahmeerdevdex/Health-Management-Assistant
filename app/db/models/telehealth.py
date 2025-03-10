from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class TelehealthSession(Base):
    """
    Represents a telehealth session between a user and a practitioner.
    """
    __tablename__ = "telehealth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    practitioner_id = Column(Integer, ForeignKey("practitioners.id"), nullable=False)
    session_status = Column(String, default="active")  
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships (Optional: If you want to access user/practitioner details)
    user = relationship("User", back_populates="telehealth_sessions")
    practitioner = relationship("Practitioner", back_populates="telehealth_sessions")
