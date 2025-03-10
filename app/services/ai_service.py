from openai import AsyncOpenAI
from app.core.config import settings
from app.db.session import SessionLocal
from app.crud.health_diary import get_health_diaries
from app.crud.medication import get_medications
import logging

logger = logging.getLogger("ai_service")

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
    Provide an AI-driven analysis of possible health insights, potential causes, and recommendations.
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
