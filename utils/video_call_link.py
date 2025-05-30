import uuid
from datetime import datetime
from datetime import datetime, date

def generate_uuid():
    """Generate a unique identifier."""
    return str(uuid.uuid4())

def format_datetime(dt: datetime) -> str:
    """Format a datetime object as a readable string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def generate_video_call_link(therapist_id: int, appointment_time: datetime) -> str:
    """
    Generate a dummy video call link for the appointment.
    """
    return f"https://videocall.example.com/{generate_uuid()}?therapist={therapist_id}&time={format_datetime(appointment_time)}"
