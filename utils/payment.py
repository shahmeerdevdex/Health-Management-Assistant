import uuid
from datetime import datetime
from datetime import datetime, date

def generate_uuid():
    """Generate a unique identifier."""
    return str(uuid.uuid4())

def format_datetime(dt: datetime) -> str:
    """Format a datetime object as a readable string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def process_payment(user_id: int, therapist_id: int, payment_details: dict) -> dict:
    """
    Dummy function to process payment using Stripe.
    Returns a success response with a fake transaction ID.
    """
    transaction_id = generate_uuid()
    return {
        "success": True,
        "transaction_id": transaction_id,
        "message": f"Payment successful for user {user_id} and therapist {therapist_id}."
    }