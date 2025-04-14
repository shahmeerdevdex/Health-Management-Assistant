from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from app.db.models.roles import user_roles
from app.db.models.caregiver import CaregiverAssignment
import enum

# Enum for user roles (Ensures values match exactly with PostgreSQL ENUM)
class UserRoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    PRIMARY_HOLDER = "PRIMARY_HOLDER"
    FAMILY_MEMBER = "FAMILY_MEMBER"
    PRACTITIONER = "PRACTITIONER"
    CAREGIVER = "CAREGIVER"
    PROFESSIONAL = "PROFESSIONAL"
    

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    role = Column(Enum(UserRoleEnum, name="userroleenum", create_type=False), nullable=False, default=UserRoleEnum.FAMILY_MEMBER)
    
    subscription_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=True)
    stripe_customer_id = Column(String, unique=True, nullable=True)  

    # Relationships  
    subscription = relationship("Subscription", back_populates="users")
    notifications = relationship("Notification", back_populates="user")
    health_diary_entries = relationship("HealthDiary", back_populates="user")
    medications = relationship("Medication", back_populates="user")  
    appointments = relationship("Appointment", back_populates="user", cascade="all, delete-orphan")
    telehealth_sessions = relationship("TelehealthSession", back_populates="user")
    chronic_monitoring = relationship("ChronicMonitoring", back_populates="patient", cascade="all, delete-orphan")
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    pharmacy_orders = relationship("PharmacyOrder", back_populates="user", cascade="all, delete-orphan")
    vaccination_records = relationship("VaccinationRecord", back_populates="user", cascade="all, delete-orphan")
    community_posts = relationship("CommunityPost", back_populates="user", cascade="all, delete-orphan")
    community_comments = relationship("CommunityComment", back_populates="user", cascade="all, delete-orphan")
    community_likes = relationship("CommunityLike", back_populates="user", cascade="all, delete-orphan")
    community_reports = relationship("CommunityReport", back_populates="user", cascade="all, delete-orphan")
    ehr_records = relationship("EHRRecord", back_populates="user", cascade="all, delete-orphan")
    emergency_health_id = relationship("EmergencyHealthID", uselist=False, back_populates="user", cascade="all, delete-orphan")
    insurance_plans = relationship("InsurancePlan", back_populates="user", cascade="all, delete-orphan")

    caregiver_assignments = relationship("CaregiverAssignment", foreign_keys=[CaregiverAssignment.caregiver_id], back_populates="caregiver", cascade="all, delete-orphan")
    patient_caregivers = relationship("CaregiverAssignment", foreign_keys=[CaregiverAssignment.patient_id], back_populates="patient", cascade="all, delete-orphan")
    
    gamification = relationship("Gamification", back_populates="user", uselist=False, cascade="all, delete-orphan")
    leaderboard = relationship("Leaderboard", back_populates="user", uselist=False, cascade="all, delete-orphan")
    therapist_appointments = relationship("TherapistAppointment", back_populates="user", cascade="all, delete-orphan")
    practitioner_relationships = relationship("Practitioner",secondary="practitioner_patient",back_populates="patients")
    
    family_members = relationship("FamilyLink",foreign_keys="[FamilyLink.user_id]",back_populates="user")
    linked_to = relationship("FamilyLink",foreign_keys="[FamilyLink.family_member_id]",back_populates="family_member")
    practitioner_profile = relationship("Practitioner", back_populates="user", uselist=False)
    sent_messages = relationship("Message", back_populates="sender", foreign_keys="[Message.sender_id]", cascade="all, delete-orphan")
    received_messages = relationship("Message", back_populates="receiver", foreign_keys="[Message.receiver_id]", cascade="all, delete-orphan")
    ehr_record = relationship("EHRRecord", back_populates="user", uselist=False)
    oauth_tokens = relationship("UserOAuthToken", back_populates="user", cascade="all, delete-orphan")
    caregiver_profile = relationship("Caregiver", uselist=False, back_populates="user")
    professional_profile = relationship("Professional", back_populates="user", uselist=False)
