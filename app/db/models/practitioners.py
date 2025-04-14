from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Practitioner(Base):
    __tablename__ = "practitioners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    contact_info = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    user = relationship("User", back_populates="practitioner_profile")
    telehealth_sessions = relationship("TelehealthSession", back_populates="practitioner")
    patients = relationship("User",secondary="practitioner_patient",back_populates="practitioner_relationships")

