from pydantic import BaseModel
from typing import List, Optional

class EmergencySupportRequest(BaseModel):
    user_id: int  # The user requesting emergency support
    latitude: float  # User's current latitude (from mobile GPS)
    longitude: float  # User's current longitude
    emergency_description: str  # Free-form input about the emergency (AI will classify this)

class EmergencyResource(BaseModel):
    name: str  # Name of the emergency resource or contact
    contact: str  # Emergency contact details (phone, website, etc.)
    description: Optional[str] = None  # Description of the resource

class EmergencySupportResponse(BaseModel):
    user_id: int
    emergency_type: str  # Detected/emerged from AI classification
    recommended_resources: List[EmergencyResource]  # Localized emergency contacts
    immediate_steps: str  # AI-generated urgent action or fallback steps
