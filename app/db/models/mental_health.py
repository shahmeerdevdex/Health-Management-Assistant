from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, JSON, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.base import Base

class TherapyType(enum.Enum):
    INDIVIDUAL = "individual"
    GROUP = "group"
    COUPLES = "couples"
    FAMILY = "family"
    CRISIS = "crisis"

class TherapyApproach(enum.Enum):
    CBT = "cognitive_behavioral"
    DBT = "dialectical_behavioral"
    PSYCHODYNAMIC = "psychodynamic"
    HUMANISTIC = "humanistic"
    MINDFULNESS = "mindfulness"
    OTHER = "other"

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
    credentials = Column(JSON, nullable=True)  # List of certifications and qualifications
    languages = Column(JSON, nullable=True)  # List of languages spoken
    specialties = Column(JSON, nullable=True)  # List of specific mental health specialties
    availability = Column(JSON, nullable=True)  # Weekly schedule
    emergency_available = Column(Boolean, default=False)  # Available for crisis situations
    therapy_types = Column(JSON, nullable=True)  # List of TherapyType values
    approaches = Column(JSON, nullable=True)  # List of TherapyApproach values
    session_duration = Column(Integer, nullable=False, default=50)  # Duration in minutes
    session_fee = Column(Float, nullable=True)
    sliding_scale = Column(Boolean, default=False)
    min_fee = Column(Float, nullable=True)
    max_fee = Column(Float, nullable=True)

    # Relationship with therapist appointments
    therapist_appointments = relationship("TherapistAppointment", back_populates="therapist", cascade="all, delete-orphan")
    user = relationship("User", back_populates="professional_profile")
    reviews = relationship("TherapistReview", back_populates="therapist", cascade="all, delete-orphan")
    appointments = relationship(
        "Appointment",
        primaryjoin="and_(foreign(Appointment.provider_id)==Professional.id, "
                   "Appointment.provider_type=='professional')",
        back_populates="professional",
        viewonly=True
    )

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
    session_type = Column(Enum(TherapyType), nullable=False)
    approach = Column(Enum(TherapyApproach), nullable=True)
    notes = Column(Text, nullable=True)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    session_summary = Column(Text, nullable=True)
    goals_discussed = Column(JSON, nullable=True)
    homework_assigned = Column(JSON, nullable=True)
    next_session_agenda = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="therapist_appointments")
    therapist = relationship("Professional", back_populates="therapist_appointments")  # Link to Professional

class MentalHealthAssessment(Base):
    """
    Stores comprehensive mental health assessments.
    """
    __tablename__ = "mental_health_assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    assessment_type = Column(String, nullable=False)  # PHQ-9, GAD-7, etc.
    scores = Column(JSON, nullable=False)  # Detailed scores for each question
    total_score = Column(Integer, nullable=False)
    risk_level = Column(String, nullable=False)  # Low, Moderate, High
    recommendations = Column(JSON, nullable=True)
    follow_up_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    therapist_id = Column(Integer, ForeignKey("professionals.id"), nullable=True)
    assessment_tools = Column(JSON, nullable=True)  # List of assessment tools used
    symptoms = Column(JSON, nullable=True)  # List of reported symptoms
    triggers = Column(JSON, nullable=True)  # Identified triggers
    coping_strategies = Column(JSON, nullable=True)  # Current coping strategies
    support_system = Column(JSON, nullable=True)  # Available support system

    # Relationships
    user = relationship("User", back_populates="mental_health_assessments")
    therapist = relationship("Professional")

class TherapistReview(Base):
    """
    Stores reviews for mental health professionals.
    """
    __tablename__ = "therapist_reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    therapist_id = Column(Integer, ForeignKey("professionals.id"), nullable=False)
    rating = Column(Float, nullable=False)
    review_text = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    helpful_votes = Column(Integer, default=0)
    verified_session = Column(Boolean, default=False)
    session_date = Column(DateTime, nullable=True)
    therapy_type = Column(Enum(TherapyType), nullable=True)
    approach = Column(Enum(TherapyApproach), nullable=True)

    # Relationships
    user = relationship("User")
    therapist = relationship("Professional", back_populates="reviews")

class MentalHealthResource(Base):
    """
    Stores mental health resources and educational content.
    """
    __tablename__ = "mental_health_resources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content_type = Column(String, nullable=False)  # Article, Video, Exercise, etc.
    content = Column(Text, nullable=False)
    target_audience = Column(JSON, nullable=True)  # Who this resource is for
    tags = Column(JSON, nullable=True)  # Topics covered
    difficulty_level = Column(String, nullable=True)  # Beginner, Intermediate, Advanced
    duration = Column(Integer, nullable=True)  # Time to complete in minutes
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    author = Column(String, nullable=True)
    source = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    related_conditions = Column(JSON, nullable=True)  # List of related mental health conditions
    estimated_time = Column(Integer, nullable=True)  # Estimated time to complete in minutes
    prerequisites = Column(JSON, nullable=True)  # List of prerequisites
    learning_objectives = Column(JSON, nullable=True)  # List of learning objectives

class CrisisIntervention(Base):
    """
    Stores crisis intervention records.
    """
    __tablename__ = "crisis_interventions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    crisis_type = Column(String, nullable=False)  # Suicidal, Anxiety Attack, etc.
    severity = Column(String, nullable=False)  # Low, Moderate, High, Emergency
    intervention_type = Column(String, nullable=False)
    responder_id = Column(Integer, ForeignKey("professionals.id"), nullable=True)
    actions_taken = Column(JSON, nullable=False)
    outcome = Column(String, nullable=False)
    follow_up_required = Column(Boolean, default=True)
    follow_up_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    emergency_services_contacted = Column(Boolean, default=False)
    safety_plan_created = Column(Boolean, default=False)
    support_network_contacted = Column(JSON, nullable=True)  # List of contacted support network members

    # Relationships
    user = relationship("User", back_populates="crisis_interventions")
    responder = relationship("Professional")
