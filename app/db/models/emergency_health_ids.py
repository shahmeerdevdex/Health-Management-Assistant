from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from app.schemas.emergency_health_ids import BloodType

class EmergencyHealthID(Base):
    __tablename__ = "emergency_health_ids"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Basic Health Information
    blood_type = Column(Enum(BloodType), nullable=True)
    allergies = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    critical_conditions = Column(Text, nullable=True)
    organ_donor_status = Column(Boolean, default=False)
    
    # Emergency Contacts
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    primary_care_physician = Column(String, nullable=True)
    physician_contact = Column(String, nullable=True)
    
    # Additional Information
    preferred_language = Column(String, nullable=True)
    insurance_provider = Column(String, nullable=True)
    insurance_number = Column(String, nullable=True)
    additional_notes = Column(Text, nullable=True)
    
    # Digital Features
    qr_code = Column(Text, nullable=True)
    qr_code_enabled = Column(Boolean, default=True)
    lock_screen_enabled = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=True)
    access_count = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="emergency_health_id")
