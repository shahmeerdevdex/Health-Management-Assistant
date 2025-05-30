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
from app.db.models.mental_health import (
    TherapistAppointment,
    Professional,
    MentalHealthResource,
    MentalHealthAssessment,
    TherapistReview,
    CrisisIntervention
)
from app.db.models.community import (
    CommunityComment,
    CommunityLike,
    CommunityPost,
    CommunityReport,
    SupportGroup,
    GroupMembership,
    ModerationStatus,
    ReportSeverity
)
from app.db.models.ehr_sync import (
    EHRRecord,
    EHRConnection,
    FHIRResourceCache,
    NationalDatabaseConnection,
    NationalDatabaseSyncRecord
)
from app.db.models.emergency_health_ids import EmergencyHealthID
from app.db.models.insurance import (
    InsurancePlan,
    OutOfPocketCost,
    MedicareClaim,
    InsuranceCoverageDetail
)
from app.db.models.subscription import SubscriptionPlan,Subscription
from app.db.models.family import FamilyLink, FamilyHealthSummary
from app.db.models.messaging import Message, MessageAuditLog
from app.db.models.oauth_token import UserOAuthToken
from app.db.models.caregiver import Caregiver,CaregiverAssignment
from app.db.models.emergency_response import (
    EmergencyResource,
    EmergencyProtocol,
    EmergencyTraining,
    EmergencyResponse,
    EmergencyTeam,
    EmergencyZone,
    EmergencyDispatch,
    EmergencyTracking,
    EmergencyResourceInventory,
    EmergencyType,
    EmergencySeverity,
    EmergencyStatus
)
from app.db.models.provider_analytics import (
    QualityMetrics,
    ProviderAnalytics,
    PopulationHealthMetrics,
    OperationalMetrics
)
from app.db.models.health_checkin import HealthCheckIn, HealthCheckInSchedule
from app.db.models.digital_wallet import (
    DigitalCredential,
    CredentialShare,
    CredentialVerification
)
from app.db.models.referral import Referral, ReferralDocument, ReferralHistory
from app.db.models.accessibility import (
    AccessibilityLog,
    UserAccessibility,
    ContentTranslation,
    VoiceCommand,
    MedicalTerm
)
from app.db.models.care_plan import (
    CarePlan,
    CarePlanDailyTask,
    CarePlanProgress,
    CarePlanExercise,
    CarePlanDiet,
    CarePlanTreatment
)
from app.db.models.national_emergency import (
    NationalEmergencyResource,
    EmergencyAlert,
    EmergencyAlertSubscription,
    EmergencyResponsePlan,
    EmergencyRegion
)
from app.db.models.referral_system import ReferralSystem, ReferralStatus
from app.db.models.provider_analytics import ProviderAnalytics
