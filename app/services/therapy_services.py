from app.schemas.therapy import TherapyGuidanceRequest, TherapyGuidanceResponse
from openai import AsyncOpenAI
from app.core.config import settings
import logging

logger = logging.getLogger("ai_services")
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def get_therapy_guidance(request: TherapyGuidanceRequest, db) -> TherapyGuidanceResponse:
    """
    Generates personalized therapy recommendations using OpenAI.
    """

    prompt = f"""
    The user is seeking non-invasive therapy recommendations for the condition: "{request.condition}".
    Please list 3–5 relevant, evidence-based therapies.
    
    Response format:
    - A comma-separated list of therapy names
    - A short paragraph explaining why these are suitable
    """

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a licensed mental and physical health therapist."},
                {"role": "user", "content": prompt}
            ]
        )
        ai_response = response.choices[0].message.content.strip()

        # Split response into list and description
        lines = ai_response.split("\n")
        therapy_list = []
        description = ""

        for line in lines:
            if "-" in line:
                therapy = line.split("-", 1)[1].strip()
                therapy_list.append(therapy)
            else:
                description += line.strip() + " "

        if not therapy_list:
            # fallback if no hyphenated list found
            therapy_list = ai_response.split("\n")[0].split(", ")

        return TherapyGuidanceResponse(
            recommended_therapies=therapy_list,
            description=description.strip()
        )

    except Exception as e:
        logger.error(f"AI therapy recommendation failed: {str(e)}")
        # Fallback
        return TherapyGuidanceResponse(
            recommended_therapies=["General Stress Management Techniques"],
            description="Unable to generate personalized therapy recommendations at this time. Please try again later."
        )
