import requests
from app.core.config import settings
import logging

logger = logging.getLogger("sms_service")

async def send_sms(phone_number: str, message: str):
    """Send an SMS notification to a user."""
    try:
        payload = {
            "api_key": settings.SMS_API_KEY,
            "phone": phone_number,
            "message": message,
        }
        response = requests.post("https://sms-provider.com/api/send", json=payload)
        response.raise_for_status()
        logger.info(f"SMS sent successfully to {phone_number}")
        return await True
    except requests.RequestException as e:
        logger.error(f"Failed to send SMS to {phone_number}: {e}")
        return await False
