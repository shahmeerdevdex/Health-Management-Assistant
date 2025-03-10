import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging

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
