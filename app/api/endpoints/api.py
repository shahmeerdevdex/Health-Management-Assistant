from fastapi import APIRouter
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
)

api_router = APIRouter()

#  Add correct prefixes for each module
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(user.router, tags=["User Management"])
api_router.include_router(health_diary.router, tags=["Health Diary"])
api_router.include_router(medications.router, tags=["Medication"])
api_router.include_router(ai_insights.router, tags=["AI Insights"])
api_router.include_router(reports.router, tags=["Reports"])
api_router.include_router(appointments.router, tags=["Appointments"])
api_router.include_router(notifications.router, tags=["Notifications"])
api_router.include_router(dashboard.router, tags=["Dashboard"])
api_router.include_router(practitioner.router, tags=["Practitioner"])
api_router.include_router(telehealth.router, tags=["Telehealth"])
