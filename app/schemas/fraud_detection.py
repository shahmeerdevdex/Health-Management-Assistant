from pydantic import BaseModel
from typing import List, Optional

class FraudDetectionRequest(BaseModel):
    user_id: int  # The user associated with the transaction
    transaction_id: str  # Stripe PaymentIntent or Charge ID (alphanumeric)
    transaction_amount: float  # The amount involved in the transaction
    transaction_type: str  # Type of transaction (e.g., "insurance claim", "medication purchase")
    transaction_date: Optional[str] = None  # Date of the transaction (ISO 8601 recommended)
    metadata: Optional[dict] = None  # Additional details about the transaction

class FraudInsight(BaseModel):
    insight: str  # AI-generated or predefined fraud detection insight

class FraudDetectionResponse(BaseModel):
    user_id: int
    transaction_id: str
    flagged: bool  # Indicates if the transaction is flagged as fraudulent
    insights: List[FraudInsight]  # Fraud analysis insights
    recommendation: str  # Suggested next steps
