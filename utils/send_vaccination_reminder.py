import uuid
from datetime import datetime
from datetime import datetime, date

def generate_uuid():
    """Generate a unique identifier."""
    return str(uuid.uuid4())

def format_datetime(dt: datetime) -> str:
    """Format a datetime object as a readable string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


async def send_sms(user_phone: str, message: str):
    """
    Dummy SMS function that logs a message instead of sending an SMS.
    """
    print(f"[SMS] Skipping actual SMS. To: {user_phone}, Message: {message}")
    return {"status": "Skipped (SMS not implemented)", "phone": user_phone}

async def send_email(user_email: str, subject: str, message: str):
    """
    Dummy email function that logs a message instead of sending an email.
    """
    print(f"[EMAIL] Skipping actual email. To: {user_email}, Subject: {subject}")
    return {"status": "Skipped (Email not implemented)", "email": user_email}


async def send_vaccination_reminder(user_email: str, user_phone: str, next_due_date: date, vaccine_name: str):
    """
    Sends a vaccination reminder to the user via email and/or SMS.
    """
    days_remaining = (next_due_date - datetime.utcnow().date()).days

 
    subject = "Vaccination Reminder"
    message = (
        f"Hello,\n\nThis is a friendly reminder that your next vaccination ({vaccine_name}) "
        f"is due on {next_due_date.strftime('%Y-%m-%d')}.\n\n"
        f"Please schedule your appointment soon.\n\nThank you!"
    )

    
    if user_email:
        try:
            await send_email(user_email, subject, message)
        except Exception as e:
            print(f"Failed to send email reminder: {e}")

    
    if user_phone:
        try:
            await send_sms(user_phone, message)
        except Exception as e:
            print(f"Failed to send SMS reminder: {e}")

    return {
        "status": "Reminder sent",
        "user_email": user_email,
        "user_phone": user_phone,
        "vaccine_name": vaccine_name,
        "due_date": next_due_date
    }