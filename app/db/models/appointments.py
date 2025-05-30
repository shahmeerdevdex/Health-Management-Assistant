from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from app.db.base import Base
import enum

class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"

class AppointmentType(str, enum.Enum):
    REGULAR = "regular"
    MENTAL_HEALTH = "mental_health"
    CRISIS = "crisis"
    ASSESSMENT = "assessment"
    MEDICAL = "medical"
    SPECIALIST = "specialist"

class ProviderType(str, enum.Enum):
    PRACTITIONER = "practitioner"  # Medical doctors
    PROFESSIONAL = "professional"  # Mental health professionals

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider_type = Column(Enum(ProviderType), nullable=False)
    provider_id = Column(Integer, nullable=False)  # Can be either practitioner_id or professional_id
    date = Column(DateTime, nullable=False)
    duration = Column(Integer, nullable=False, default=30)  # Duration in minutes
    location = Column(String, nullable=True)
    appointment_type = Column(Enum(AppointmentType), nullable=False, default=AppointmentType.REGULAR)
    status = Column(Enum(AppointmentStatus), nullable=False, default=AppointmentStatus.SCHEDULED)
    notes = Column(String, nullable=True)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    session_summary = Column(String, nullable=True)
    goals_discussed = Column(JSON, nullable=True)  # List of goals
    homework_assigned = Column(JSON, nullable=True)  # List of homework items
    next_session_agenda = Column(String, nullable=True)
    video_call_link = Column(String, nullable=True)
    reminder_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="appointments")
    
    # Dynamic relationship with Practitioner
    practitioner = relationship(
        "Practitioner",
        primaryjoin="and_(foreign(Appointment.provider_id)==Practitioner.id, "
                   "Appointment.provider_type=='practitioner')",
        back_populates="appointments",
        viewonly=True
    )
    
    # Dynamic relationship with Professional
    professional = relationship(
        "Professional",
        primaryjoin="and_(foreign(Appointment.provider_id)==Professional.id, "
                   "Appointment.provider_type=='professional')",
        back_populates="appointments",
        viewonly=True
    )

    @hybrid_property
    def provider(self):
        """Get the provider (either practitioner or professional) based on provider_type."""
        if self.provider_type == ProviderType.PRACTITIONER:
            return self.practitioner
        return self.professional
