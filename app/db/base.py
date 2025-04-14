from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): 
    pass


from app.db.models.user import User
from app.db.models.appointments import Appointment
from app.db.models.health_diary import HealthDiary
from app.db.models.health_tips import HealthTip
from app.db.models.medication import Medication
from app.db.models.medication_logs import MedicationLog
from app.db.models.notifications import Notification
from app.db.models.practitioner_patient import practitioner_patient
from app.db.models.reports import Report
from app.db.models.roles import Role
from app.db.models.symptom_analysis import SymptomAnalysis
from app.db.models.practitioners import Practitioner
from app.db.models.telehealth import TelehealthSession
from app.db.models.monitoring import ChronicMonitoring
from app.db.models.pharmacy import PharmacyOrder
from app.db.models.vaccination import VaccinationRecord
from app.db.models.gamification import Gamification,Leaderboard
from app.db.models.mental_health import TherapistAppointment,Professional
from app.db.models.community import CommunityComment,CommunityLike,CommunityPost,CommunityReport
from app.db.models.ehr_sync import EHRRecord
from app.db.models.emergency_health_ids import EmergencyHealthID
from app.db.models.insurance import InsurancePlan
from app.db.models.subscription import SubscriptionPlan,Subscription
from app.db.models.family import FamilyLink
from app.db.models.referral_system import Referral
from app.db.models.messaging import Message
from app.db.models.oauth_token import UserOAuthToken
from app.db.models.caregiver import Caregiver,CaregiverAssignment
