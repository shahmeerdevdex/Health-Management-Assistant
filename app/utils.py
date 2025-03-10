import uuid
from datetime import datetime

def generate_uuid():
    """Generate a unique identifier."""
    return str(uuid.uuid4())

def format_datetime(dt: datetime) -> str:
    """Format a datetime object as a readable string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")
