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
