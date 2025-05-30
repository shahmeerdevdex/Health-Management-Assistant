from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.db.base import Base

class FamilyLink(Base):
    __tablename__ = "family_links"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    family_member_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    relationship_type = Column(String, nullable=False)  # e.g., "parent", "child", "spouse"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sharing_preferences = Column(JSON, nullable=True)  # Controls what health data is shared

    user = relationship("User", foreign_keys=[user_id], back_populates="family_members")
    family_member = relationship("User", foreign_keys=[family_member_id], back_populates="linked_to")
    health_summaries = relationship("FamilyHealthSummary", back_populates="family_link", cascade="all, delete-orphan")

class FamilyHealthSummary(Base):
    __tablename__ = "family_health_summaries"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_links.id"), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Comprehensive health summary
    overall_health_status = Column(String, nullable=True)  # e.g., "good", "fair", "poor"
    active_conditions = Column(JSON, nullable=True)  # List of current health conditions
    medications = Column(JSON, nullable=True)  # Current medications across family
    allergies = Column(JSON, nullable=True)  # Family-wide allergy information
    upcoming_appointments = Column(JSON, nullable=True)  # All family appointments
    recent_health_events = Column(JSON, nullable=True)  # Recent health incidents
    risk_factors = Column(JSON, nullable=True)  # Family health risk factors
    preventive_care = Column(JSON, nullable=True)  # Preventive care needs
    lifestyle_factors = Column(JSON, nullable=True)  # Family lifestyle information
    emergency_contacts = Column(JSON, nullable=True)  # Emergency contact information
    care_coordination = Column(JSON, nullable=True)  # Care coordination details
    notes = Column(Text, nullable=True)  # Additional family health notes

    # Relationships
    family_link = relationship("FamilyLink", back_populates="health_summaries")
