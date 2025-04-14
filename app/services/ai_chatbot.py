import openai
from app.core.config import settings
from app.crud.user import get_user
from sqlalchemy.ext.asyncio import AsyncSession

openai_client = openai.AsyncClient(api_key=settings.OPENAI_API_KEY)

async def generate_health_advice(user_id: int, user_message: str, db: AsyncSession):
    """Generate AI-powered health advice based on user input and history."""

    user = await get_user(db, user_id)
    if not user:
        return "User not found. Please ensure you are logged in."

    prompt = f"""
You are an AI health assistant providing general wellness guidance.

User Info:
- Name: {user.full_name}
- Role: {user.role}
- Past symptoms: {user.health_diary if hasattr(user, 'health_diary') else "None"}

User says: {user_message}

If symptoms indicate a possible emergency, include basic first-aid steps and recommend seeking medical attention.

Otherwise, offer concise, relevant health advice based on the symptom.

Avoid vague emotional advice. Do not assume mental health context unless clearly asked.
"""


    response = await openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()
