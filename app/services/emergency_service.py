from sqlalchemy.orm import Session
from app.schemas.emergency import EmergencySupportRequest, EmergencySupportResponse, EmergencyResource
from app.core.config import settings
from app.services.ai_services import classify_emergency_type
import requests
import logging

logger = logging.getLogger("emergency_support")

# Helper: Use Mapbox to convert lat/lng → country code
async def get_country_from_coordinates(lat: float, lon: float) -> str:
    try:
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{lon},{lat}.json"
        params = {"access_token": settings.MAPBOX_API_KEY}
        response = requests.get(url, params=params)
        data = response.json()

        for feature in data.get("features", []):
            if "country" in feature["place_type"]:
                return feature["properties"].get("short_code", "US").upper()  # ISO country code

    except Exception as e:
        logger.error(f"Mapbox error: {str(e)}")

    return "US"  # Fallback to US

# Hardcoded global resource directory
COUNTRY_RESOURCES = {
    "US": {
        "mental health crisis": [
            EmergencyResource(name="988 Suicide & Crisis Lifeline", contact="988", description="24/7 mental health support"),
            EmergencyResource(name="Crisis Text Line", contact="Text HOME to 741741", description="Text-based crisis counseling")
        ],
        "medical emergency": [
            EmergencyResource(name="Emergency Medical Services", contact="911", description="Call for urgent medical help")
        ],
        "domestic violence": [
            EmergencyResource(name="National Domestic Violence Hotline", contact="800-799-7233", description="24/7 support for abuse victims")
        ]
    },
    "UK": {
        "mental health crisis": [
            EmergencyResource(name="Samaritans", contact="116 123", description="Free 24/7 support for mental health")
        ],
        "medical emergency": [
            EmergencyResource(name="Emergency Services", contact="999", description="Call for ambulance/fire/police")
        ],
        "domestic violence": [
            EmergencyResource(name="Refuge", contact="0808 2000 247", description="24-hour domestic abuse support")
        ]
    },
    # Add more countries as needed...
}


async def process_emergency_support(request: EmergencySupportRequest, db: Session) -> EmergencySupportResponse:
    """
    Dynamically detects emergency type via AI and provides country-specific emergency support resources.
    """
    resources = []
    immediate_steps = "Stay calm and follow instructions below."

    # 1. Detect user's country
    country_code = await get_country_from_coordinates(request.latitude, request.longitude)
    logger.info(f"Resolved country code: {country_code}")

    # 2. Use AI to classify emergency type
    emergency_type, ai_steps = await classify_emergency_type(request.emergency_description)
    logger.info(f"AI classified emergency type: {emergency_type}")

    # 3. Fetch localized resources
    country_info = COUNTRY_RESOURCES.get(country_code, COUNTRY_RESOURCES["US"])
    resources = country_info.get(emergency_type, [])

    if not resources:
        resources = [EmergencyResource(name="Local Emergency", contact="911", description="Call for urgent assistance")]

    return EmergencySupportResponse(
        user_id=request.user_id,
        emergency_type=emergency_type,
        recommended_resources=resources,
        immediate_steps=ai_steps
    )
