from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.health_diary import get_latest_entry
from app.crud.medication import get_today_medications as get_pending_medications
from app.crud.appointment import get_upcoming_appointments
from app.crud.notification import get_notifications
from app.services.ai_services import detect_health_patterns
from app.crud.subscription import get_user_subscription_status

async def build_user_dashboard(db: AsyncSession, user_id: int):
    mood_entry = await get_latest_entry(db, user_id)
    medications = await get_pending_medications(db, user_id)
    appointments = await get_upcoming_appointments(db, user_id)
    alerts = await get_notifications(db, user_id)
    ai_insights = await detect_health_patterns(user_id)
    subscription = await get_user_subscription_status(db, user_id)

    return {
        "latest_mood": mood_entry,
        "upcoming_medications": medications,
        "next_appointments": appointments,
        "notifications": alerts,
        "ai_insights": ai_insights,
        "subscription_plan": subscription
    }
