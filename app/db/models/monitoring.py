from sqlalchemy import Column, String, Integer, Float, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class ChronicMonitoring(Base):
    __tablename__ = "chronic_monitoring"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    condition = Column(String, nullable=False)  # e.g., "diabetes", "hypertension"
    blood_pressure = Column(JSON, nullable=True)  # List of systolic & diastolic readings
    blood_sugar = Column(JSON, nullable=True)  # List of glucose levels over time
    heart_rate = Column(JSON, nullable=True)  # List of heart rate readings
    weight = Column(JSON, nullable=True)  # List of weight readings
    medications = Column(JSON, nullable=True)  # List of prescribed medications
    recorded_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("User", back_populates="chronic_monitoring")
