import uuid
from datetime import datetime
from datetime import datetime, date

def generate_uuid():
    """Generate a unique identifier."""
    return str(uuid.uuid4())

def format_datetime(dt: datetime) -> str:
    """Format a datetime object as a readable string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

async def send_email(user_email: str, subject: str, message: str):
    """
    Dummy email function that logs a message instead of sending an email.
    """
    print(f"[EMAIL] Skipping actual email. To: {user_email}, Subject: {subject}")
    return {"status": "Skipped (Email not implemented)", "email": user_email}
