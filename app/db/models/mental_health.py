from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Professional(Base):
    """
    Stores therapist/professional details.
    """
    __tablename__ = "professionals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    location = Column(String, nullable=False)
    accepts_insurance = Column(Boolean, default=False)
    online_available = Column(Boolean, default=True)
    contact_info = Column(String, nullable=False)
    rating = Column(Float, default=0.0)  # Optional: Therapist rating system

    # Relationship with therapist appointments
    appointments = relationship("TherapistAppointment", back_populates="therapist", cascade="all, delete-orphan")
    user = relationship("User", back_populates="professional_profile")

class TherapistAppointment(Base):
    """
    Stores therapist-specific appointments.
    """
    __tablename__ = "therapist_appointments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    therapist_id = Column(Integer, ForeignKey("professionals.id"), nullable=False)  # Links to `Professional`
    date_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(String, nullable=False, default="Pending")  # Status: Pending, Confirmed, Completed
    payment_status = Column(String, nullable=False, default="Pending")  # Payment: Pending, Paid, Canceled
    video_call_link = Column(String, nullable=True)  # For online sessions

    # Relationships
    user = relationship("User", back_populates="therapist_appointments")
    therapist = relationship("Professional", back_populates="appointments")  # Link to Professional
