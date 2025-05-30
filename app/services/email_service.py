import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("email_service")

async def send_email(recipient: str, subject: str, body: str):
    """Send an email notification to a user."""
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_USERNAME
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.starttls()
        server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
        server.sendmail(settings.EMAIL_USERNAME, recipient, msg.as_string())
        server.quit()
        logger.info(f"Email sent successfully to {recipient}")
        return await True
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {e}")
        return await False

async def send_email_alert(
    recipient: str,
    alert_type: str,
    message: str,
    priority: str = "normal",
    meta_data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send an alert email to a user with additional context and priority.
    
    Args:
        recipient: The recipient's email address
        alert_type: Type of alert (e.g., 'health', 'appointment', 'medication')
        message: The alert message to send
        priority: Alert priority ('low', 'normal', 'high', 'urgent')
        metadata: Additional context data for the alert
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Format the subject with priority and type
        subject = f"[{priority.upper()}] {alert_type.upper()} Alert"
        
        # Format the email body
        body = f"""
        Alert Type: {alert_type.upper()}
        Priority: {priority.upper()}
        
        Message:
        {message}
        """
        
        # Add metadata to the body if provided
        if meta_data:
            body += "\nAdditional Details:\n"
            for key, value in meta_data.items():
                body += f"{key}: {value}\n"
        
        # Send the email
        success = await send_email(recipient, subject, body)
        
        if success:
            logger.info(f"Alert email sent successfully to {recipient} - Type: {alert_type}, Priority: {priority}")
        else:
            logger.error(f"Failed to send alert email to {recipient}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending alert email to {recipient}: {str(e)}")
        return False
