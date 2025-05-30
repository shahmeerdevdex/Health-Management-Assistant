from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum, Boolean, Text, Float
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.schemas.national_emergency import EmergencyAlertType, EmergencySeverity
from datetime import datetime

class EmergencyAlert(Base):
    __tablename__ = "emergency_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String, unique=True, nullable=False)
    type = Column(Enum(EmergencyAlertType), nullable=False)
    severity = Column(Enum(EmergencySeverity), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    affected_regions = Column(JSON)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    source = Column(String, nullable=False)
    official_guidance = Column(JSON)
    resources = Column(JSON)
    status = Column(String, default="active")
    additional_info = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscriptions = relationship("EmergencyAlertSubscription", back_populates="alert")
    response_plans = relationship("EmergencyResponsePlan", back_populates="alert")

class EmergencyAlertSubscription(Base):
    __tablename__ = "emergency_alert_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alert_id = Column(Integer, ForeignKey("emergency_alerts.id"), nullable=False)
    alert_types = Column(JSON)
    regions = Column(JSON)
    severity_threshold = Column(Enum(EmergencySeverity), nullable=False)
    notification_preferences = Column(JSON)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="emergency_subscriptions")
    alert = relationship("EmergencyAlert", back_populates="subscriptions")

class EmergencyResponsePlan(Base):
    __tablename__ = "emergency_response_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(String, unique=True, nullable=False)
    alert_id = Column(Integer, ForeignKey("emergency_alerts.id"), nullable=False)
    alert_type = Column(Enum(EmergencyAlertType), nullable=False)
    severity_levels = Column(JSON)
    immediate_actions = Column(JSON)
    resource_requirements = Column(JSON)
    communication_protocols = Column(JSON)
    evacuation_procedures = Column(JSON)
    medical_response = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    alert = relationship("EmergencyAlert", back_populates="response_plans")

class NationalEmergencyResource(Base):
    __tablename__ = "national_emergency_resources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    contact = Column(String, nullable=False)
    description = Column(Text)
    location = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    capacity = Column(Integer)
    status = Column(String, default="available")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EmergencyRegion(Base):
    __tablename__ = "emergency_regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    affected_areas = Column(JSON)
    population_impact = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 