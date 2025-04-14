from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class EmergencyHealthID(Base):
    __tablename__ = "emergency_health_ids"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    allergies = Column(String, nullable=True)
    medications = Column(String, nullable=True)
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    critical_conditions = Column(String, nullable=True)

    user = relationship("User", back_populates="emergency_health_id")
