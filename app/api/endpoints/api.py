from fastapi import APIRouter

api_router = APIRouter()

from app.api.endpoints import (
    auth,
    user,
    health_diary,
    medications,
    ai_insights,
    reports,
    appointments,
    notifications,
    dashboard,
    practitioner,
    telehealth,
    therapy,
    wearables,
    monitoring,
    gamification,
    caregiver,
    marketplace,
    diagnostics,
    sustainability,
    fraud_detection,
    emergency,
    pharmacy,
    vaccination,
    roles,
    community,
    emergency_health_ids,
    insurance,
    subscription,
    payment,
    chatbot,
    locate_health_services,
    voice_command,
    ai_mood_guide,
    webhook,
    community_groups,
    family,
    ehr_sync,
    Registration_Login
)

api_router = APIRouter()

api_router.include_router(Registration_Login.router, prefix="/api/v1/registration_login", tags=["Registration & Login"])
api_router.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
api_router.include_router(webhook.router, prefix="/api/v1/webhook", tags=["WebHook"])
api_router.include_router(subscription.router, prefix="/api/v1/subscription", tags=["Subscription"])
api_router.include_router(payment.router, prefix="/api/v1/payment", tags=["Payment"])
api_router.include_router(roles.router, prefix="/api/v1/roles", tags=["Roles"])
api_router.include_router(user.router, prefix="/api/v1/users", tags=["User Management"])
api_router.include_router(health_diary.router, prefix="/api/v1/health-diary", tags=["Health Diary"])
api_router.include_router(medications.router, prefix="/api/v1/medications", tags=["Medication"])
api_router.include_router(ai_insights.router, prefix="/api/v1/ai", tags=["AI Insights"])
api_router.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
api_router.include_router(appointments.router, prefix="/api/v1/appointments", tags=["Appointments"])
api_router.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
api_router.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
api_router.include_router(practitioner.router, prefix="/api/v1/practitioner", tags=["Practitioner"])
api_router.include_router(telehealth.router, prefix="/api/v1/telehealth", tags=["Telehealth"])
api_router.include_router(therapy.router, prefix="/api/v1/therapy", tags=["Therapy"])
api_router.include_router(wearables.router, prefix="/api/v1/wearables", tags=["Wearables"])
api_router.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])
api_router.include_router(gamification.router, prefix="/api/v1/gamification", tags=["Gamification"])
api_router.include_router(caregiver.router, prefix="/api/v1/caregiver", tags=["CareGiver"])
api_router.include_router(marketplace.router, prefix="/api/v1/marketplace", tags=["MarketPlace"])
api_router.include_router(sustainability.router, prefix="/api/v1/sustainability", tags=["Sustainability"])
api_router.include_router(fraud_detection.router, prefix="/api/v1/fraud_dedection", tags=["Fraud Dedection"])
api_router.include_router(emergency.router, prefix="/api/v1/emergency", tags=["Emergency"])
api_router.include_router(pharmacy.router, prefix="/api/v1/pharmacy", tags=["Pharmacy-Orders"])
api_router.include_router(vaccination.router, prefix="/api/v1/vaccination", tags=["Vaccination"])
api_router.include_router(community.router, prefix="/api/v1/community", tags=["Community"])
api_router.include_router(community_groups.router, prefix="/api/v1/community_groups", tags=["Community Groups"])
api_router.include_router(emergency_health_ids.router, prefix="/api/v1/emergency_health_id", tags=["Emergency Health ID"])
api_router.include_router(insurance.router, prefix="/api/v1/insurance", tags=["Insurance"])
api_router.include_router(chatbot.router, prefix="/api/v1/chatbot", tags=["AI ChatBot"])
api_router.include_router(locate_health_services.router, prefix="/api/v1/locate_health_services", tags=["Locate Health Services"])
api_router.include_router(diagnostics.router, prefix="/api/v1/diagnostics", tags=["Diagnostics"])
api_router.include_router(voice_command.router, prefix="/api/v1/voice_services", tags=["Voice Services"])
api_router.include_router(ai_mood_guide.router, prefix="/api/v1/ai_mood_guide", tags=["AI Mood Guide"])
api_router.include_router(family.router, prefix="/api/v1/family", tags=["Family Links"])
api_router.include_router(ehr_sync.router, prefix="/api/v1/ehr_sync", tags=["EHR Sync"])
