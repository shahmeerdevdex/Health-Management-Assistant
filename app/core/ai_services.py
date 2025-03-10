from openai import AsyncOpenAI
from app.core.config import settings
from app.db.session import SessionLocal
from app.crud.health_diary import get_health_diaries
from app.crud.medication import get_medications
import logging

logger = logging.getLogger("ai_services")

# Create OpenAI client instance
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def analyze_symptoms(user_id: int):
    """Analyze user symptoms and provide AI-driven insights."""
    async with SessionLocal() as db:
        health_entries = await get_health_diaries(db, user_id)

    if not health_entries:
        return "No recent health entries found."

    symptom_text = "\n".join([f"- {entry.symptoms}" for entry in health_entries[-5:]])

    prompt = f"""
    The user has reported the following symptoms recently:
    {symptom_text}

    Based on this, provide an AI-driven analysis of possible health insights, potential causes, and recommendations.
    """

    try:
        response = await client.chat.completions.create(  
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a medical AI assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        ai_analysis = response.choices[0].message.content
        logger.info(f"AI Symptom Analysis for User {user_id}: {ai_analysis}")
        return ai_analysis

    except Exception as e:
        logger.error(f"Error in AI symptom analysis: {str(e)}")
        return "An error occurred while processing AI analysis."


async def get_personalized_health_tips(user_id: int):
    """Fetch user medication details and provide personalized health tips."""
    async with SessionLocal() as db:
        medications = await get_medications(db, user_id)

    if not medications:
        return "No medications found for this user."

    med_text = "\n".join([f"- {med.name} ({med.dosage})" for med in medications])

    prompt = f"""
    The user is currently taking the following medications:
    {med_text}

    Provide daily health tips that complement their medication routine and promote overall well-being.
    """

    try:
        response = await client.chat.completions.create(  
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a health assistant providing wellness tips."},
                {"role": "user", "content": prompt}
            ]
        )
        health_tips = response.choices[0].message.content
        logger.info(f"AI Health Tips for User {user_id}: {health_tips}")
        return health_tips

    except Exception as e:
        logger.error(f"Error in AI health tips generation: {str(e)}")
        return "An error occurred while generating AI health tips."


async def detect_health_patterns(user_id: int):
    """Analyze past health diary entries to detect symptom patterns."""
    async with SessionLocal() as db:
        health_entries = await get_health_diaries(db, user_id)

    if not health_entries or len(health_entries) < 5:
        return "Not enough data for pattern analysis."

    symptoms_log = "\n".join([f"{entry.date}: {entry.symptoms}" for entry in health_entries])

    prompt = f"""
    The following symptoms have been recorded by the user:
    {symptoms_log}

    Detect any patterns in these symptoms that may indicate underlying health concerns.
    """

    try:
        response = await client.chat.completions.create(  
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a health AI detecting trends in medical symptoms."},
                {"role": "user", "content": prompt}
            ]
        )
        pattern_analysis = response.choices[0].message.content
        logger.info(f"AI Pattern Analysis for User {user_id}: {pattern_analysis}")
        return pattern_analysis  

    except Exception as e:
        logger.error(f"Error in AI health pattern detection: {str(e)}")
        return "An error occurred while analyzing health patterns."
