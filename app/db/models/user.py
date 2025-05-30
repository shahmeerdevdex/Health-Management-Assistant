from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from app.db.models.roles import user_roles
from app.db.models.caregiver import CaregiverAssignment
import enum
from app.schemas.user import UserRoleInput

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    role = Column(Enum(UserRoleInput, name="UserRoleInput", create_type=True), nullable=False, default=UserRoleInput.FAMILY_MEMBER)
    date_of_birth = Column(Date, nullable=False)
    
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
    community_posts = relationship("CommunityPost", foreign_keys="[CommunityPost.user_id]", back_populates="user", cascade="all, delete-orphan")
    community_comments = relationship("CommunityComment", foreign_keys="[CommunityComment.user_id]", back_populates="user", cascade="all, delete-orphan")
    community_likes = relationship("CommunityLike", back_populates="user", cascade="all, delete-orphan")
    community_reports = relationship("CommunityReport", foreign_keys="[CommunityReport.user_id]", back_populates="user", cascade="all, delete-orphan")
    ehr_records = relationship("EHRRecord", back_populates="user", cascade="all, delete-orphan")
    ehr_connections = relationship("EHRConnection", back_populates="user", cascade="all, delete-orphan")
    emergency_health_id = relationship("EmergencyHealthID", uselist=False, back_populates="user", cascade="all, delete-orphan")
    insurance_plans = relationship("InsurancePlan", back_populates="user", cascade="all, delete-orphan")
    mental_health_assessments = relationship("MentalHealthAssessment", back_populates="user", cascade="all, delete-orphan")
    crisis_interventions = relationship("CrisisIntervention", back_populates="user", cascade="all, delete-orphan")
    group_memberships = relationship("GroupMembership", foreign_keys="[GroupMembership.user_id]", back_populates="user", cascade="all, delete-orphan")
    health_checkins = relationship("HealthCheckIn", back_populates="user", cascade="all, delete-orphan")
    checkin_schedule = relationship("HealthCheckInSchedule", back_populates="user", cascade="all, delete-orphan")
    population_health_metrics = relationship("PopulationHealthMetrics", back_populates="provider", cascade="all, delete-orphan")
    quality_metrics = relationship("QualityMetrics", back_populates="provider", cascade="all, delete-orphan")
    emergency_training = relationship("EmergencyTraining", back_populates="user", cascade="all, delete-orphan")
    emergency_subscriptions = relationship("EmergencyAlertSubscription", back_populates="user", cascade="all, delete-orphan")
    emergency_responses = relationship("EmergencyResponse", foreign_keys="[EmergencyResponse.user_id]", back_populates="user", cascade="all, delete-orphan")
    received_referrals = relationship("Referral", foreign_keys="[Referral.patient_id]", back_populates="patient", cascade="all, delete-orphan")
    sent_referrals = relationship("Referral", foreign_keys="[Referral.from_practitioner_id]", back_populates="from_practitioner", cascade="all, delete-orphan")
    therapist_reviews = relationship("TherapistReview", back_populates="user", cascade="all, delete-orphan")
    provider_analytics = relationship("ProviderAnalytics", back_populates="provider", cascade="all, delete-orphan")
    operational_metrics = relationship("OperationalMetrics", back_populates="provider", cascade="all, delete-orphan")
    digital_credentials = relationship("DigitalCredential", back_populates="user", cascade="all, delete-orphan")
    accessibility_preferences = relationship("UserAccessibility", back_populates="user", uselist=False, cascade="all, delete-orphan")
    accessibility_logs = relationship("AccessibilityLog", back_populates="user", cascade="all, delete-orphan")
    care_plans = relationship("CarePlan", foreign_keys="[CarePlan.user_id]", back_populates="user", cascade="all, delete-orphan")
    created_care_plans = relationship("CarePlan", foreign_keys="[CarePlan.practitioner_id]", back_populates="practitioner", cascade="all, delete-orphan")
    symptom_analyses = relationship("SymptomAnalysis", back_populates="user", cascade="all, delete-orphan")
    medication_logs = relationship("MedicationLog", back_populates="user", cascade="all, delete-orphan")
    health_tips = relationship("HealthTip", back_populates="user", cascade="all, delete-orphan")

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
    ehr_record = relationship("EHRRecord", back_populates="user", uselist=False, overlaps="ehr_records")
    oauth_tokens = relationship("UserOAuthToken", back_populates="user", cascade="all, delete-orphan")
    caregiver_profile = relationship("Caregiver", uselist=False, back_populates="user")
    professional_profile = relationship("Professional", back_populates="user", uselist=False)
    assigned_resources = relationship("EmergencyResource",back_populates="user",foreign_keys="[EmergencyResource.assigned_user_id]")
    responder_responses = relationship("EmergencyResponse",foreign_keys="[EmergencyResponse.assigned_to]",back_populates="responder")
    led_teams = relationship("EmergencyTeam", back_populates="leader", cascade="all, delete-orphan")
    teams = relationship("EmergencyTeam", secondary="team_members", back_populates="members")
    translations = relationship("ContentTranslation", back_populates="user", cascade="all, delete-orphan")
    voice_commands = relationship("VoiceCommand", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("ProviderAnalytics", back_populates="provider", overlaps="provider_analytics")