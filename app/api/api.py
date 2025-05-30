from fastapi import APIRouter
from app.api.endpoints import (
    # Authentication & User Management
    auth,
    Registration_Login,
    user,
    roles,
    
    # Health Management
    health_diary,
    health_checkin,
    medications,
    appointments,
    care_plan,
    diagnostics,
    monitoring,
    
    # Mental Health & Therapy
    mental_health,
    therapy,
    ai_mood_guide,
    
    # Emergency & Safety
    emergency_response,
    emergency_alert,
    emergency_health_ids,
    
    # Communication & Support
    notifications,
    chatbot,
    voice_command,
    telehealth,
    community,
    community_groups,
    family,
    caregiver,
    
    # Healthcare Services
    practitioner,
    pharmacy,
    insurance,
    vaccination,
    locate_health_services,
    ehr_sync,
    
    # Analytics & Insights
    provider_analytics,
    ai_insights,
    dashboard,
    
    # Wearables & Integration
    wearables,
    webhook,
    
    # Additional Features
    accessibility,
    gamification,
    fraud_detection,
    payment,
    subscription,
    digital_wallet,
    national_emergency,
    offline_sync,
    reports
    
)

api_router = APIRouter()

# Authentication & User Management
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(Registration_Login.router, prefix="/registration", tags=["Registration"])
api_router.include_router(user.router, prefix="/users", tags=["Users"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])

# Health Management
api_router.include_router(health_diary.router, prefix="/health-diary", tags=["Health Diary"])
api_router.include_router(health_checkin.router, prefix="/health-checkin", tags=["Health Check-in"])
api_router.include_router(medications.router, prefix="/medications", tags=["Medications"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
api_router.include_router(care_plan.router, prefix="/care-plan", tags=["Care Plan"])
api_router.include_router(diagnostics.router, prefix="/diagnostics", tags=["Diagnostics"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])

# Mental Health & Therapy
api_router.include_router(mental_health.router, prefix="/mental-health", tags=["Mental Health"])
api_router.include_router(therapy.router, prefix="/therapy", tags=["Therapy"])
api_router.include_router(ai_mood_guide.router, prefix="/mood-guide", tags=["Mood Guide"])

# Emergency & Safety
api_router.include_router(emergency_response.router, prefix="/emergency-response", tags=["Emergency"])
api_router.include_router(emergency_alert.router, prefix="/emergency-alert", tags=["Emergency Alert"])
api_router.include_router(emergency_health_ids.router, prefix="/emergency-ids", tags=["Emergency IDs"])

# Communication & Support
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(chatbot.router, prefix="/chatbot", tags=["Chatbot"])
api_router.include_router(voice_command.router, prefix="/voice", tags=["Voice Commands"])
api_router.include_router(telehealth.router, prefix="/telehealth", tags=["Telehealth"])
api_router.include_router(community.router, prefix="/community", tags=["Community"])
api_router.include_router(community_groups.router, prefix="/community-groups", tags=["Community Groups"])
api_router.include_router(family.router, prefix="/family", tags=["Family"])
api_router.include_router(caregiver.router, prefix="/caregiver", tags=["Caregiver"])

# Healthcare Services
api_router.include_router(practitioner.router, prefix="/practitioner", tags=["Practitioner"])
api_router.include_router(pharmacy.router, prefix="/pharmacy", tags=["Pharmacy"])
api_router.include_router(insurance.router, prefix="/insurance", tags=["Insurance"])
api_router.include_router(vaccination.router, prefix="/vaccination", tags=["Vaccination"])
api_router.include_router(locate_health_services.router, prefix="/health-services", tags=["Health Services"])
api_router.include_router(ehr_sync.router, prefix="/ehr", tags=["EHR Sync"])

# Analytics & Insights
api_router.include_router(provider_analytics.router, prefix="/provider-analytics", tags=["Provider Analytics"])
api_router.include_router(ai_insights.router, prefix="/ai-insights", tags=["AI Insights"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

# Wearables & Integration
api_router.include_router(wearables.router, prefix="/wearables", tags=["Wearables"])
api_router.include_router(webhook.router, prefix="/webhook", tags=["Webhooks"])

# Additional Features
api_router.include_router(accessibility.router, prefix="/accessibility", tags=["Accessibility"])
api_router.include_router(gamification.router, prefix="/gamification", tags=["Gamification"])
api_router.include_router(fraud_detection.router, prefix="/fraud-detection", tags=["Fraud Detection"])
api_router.include_router(payment.router, prefix="/payment", tags=["Payment"])
api_router.include_router(subscription.router, prefix="/subscription", tags=["Subscription"])
api_router.include_router(digital_wallet.router, prefix="/wallet", tags=["digital-wallet"])
api_router.include_router(national_emergency.router, prefix="/national-emergency", tags=["national-emergency"]) 
api_router.include_router(offline_sync.router, prefix="/offline-sync", tags=["offline-sync"]) 
api_router.include_router(reports.router, prefix="/reports", tags=["reports"]) 