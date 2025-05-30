import requests
from app.core.config import settings
import logging
from typing import Optional, Dict, Any

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

async def send_sms_alert(
    phone_number: str,
    alert_type: str,
    message: str,
    priority: str = "normal",
    meta_data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send an alert SMS to a user with additional context and priority.
    
    Args:
        phone_number: The recipient's phone number
        alert_type: Type of alert (e.g., 'health', 'appointment', 'medication')
        message: The alert message to send
        priority: Alert priority ('low', 'normal', 'high', 'urgent')
        metadata: Additional context data for the alert
    
    Returns:
        bool: True if SMS was sent successfully, False otherwise
    """
    try:
        # Format the alert message with priority and type
        formatted_message = f"[{priority.upper()}] {alert_type.upper()} Alert: {message}"
        
        # Add metadata to the message if provided
        if meta_data:
            metadata_str = " | ".join(f"{k}: {v}" for k, v in meta_data.items())
            formatted_message += f"\nDetails: {metadata_str}"
        
        # Send the SMS
        success = await send_sms(phone_number, formatted_message)
        
        if success:
            logger.info(f"Alert SMS sent successfully to {phone_number} - Type: {alert_type}, Priority: {priority}")
        else:
            logger.error(f"Failed to send alert SMS to {phone_number}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending alert SMS to {phone_number}: {str(e)}")
        return False
