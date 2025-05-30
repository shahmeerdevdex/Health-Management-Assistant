from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Caregiver(Base):
    __tablename__ = "caregivers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="caregiver_profile")



class CaregiverAssignment(Base):
    __tablename__ = "caregiver_assignments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    caregiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    tasks = Column(JSON, nullable=True)  # List of caregiving tasks
    schedule = Column(String, nullable=True)  # Caregiving schedule details
    emergency_contact = Column(String, nullable=True)  # Emergency contact information
    assigned_at = Column(DateTime, default=datetime.utcnow)
    
    appointment_history = Column(JSON, nullable=True)  # Past and upcoming appointments
    medication_tracking = Column(JSON, nullable=True)  # Medication logs
    monitoring_data = Column(JSON, nullable=True)  # Health monitoring
    financial_support = Column(JSON, nullable=True)  # NDIS or financial details

    # Bidirectional Relationships
    caregiver = relationship("User", foreign_keys=[caregiver_id], back_populates="caregiver_assignments")
    patient = relationship("User", foreign_keys=[patient_id], back_populates="patient_caregivers")
