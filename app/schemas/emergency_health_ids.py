from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class BloodType(str, Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"

class EmergencyHealthIDCreate(BaseModel):
    blood_type: Optional[BloodType] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    critical_conditions: Optional[str] = None
    organ_donor_status: Optional[bool] = False
    preferred_language: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_number: Optional[str] = None
    primary_care_physician: Optional[str] = None
    physician_contact: Optional[str] = None
    additional_notes: Optional[str] = None
    qr_code_enabled: bool = True
    lock_screen_enabled: bool = True

class EmergencyHealthIDResponse(EmergencyHealthIDCreate):
    id: int
    user_id: int
    qr_code: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: Optional[datetime] = None
    access_count: int = 0

    class Config:
        from_attributes = True

class EmergencyHealthIDWallet(EmergencyHealthIDResponse):
    """Format for digital wallet integration"""
    wallet_format: Dict[str, Any] = Field(default_factory=dict)
    pass_type_identifier: str = "pass.com.health.emergency.id"
    team_identifier: str = "YOUR_TEAM_ID"
    organization_name: str = "Health Management Assistant"
    description: str = "Emergency Health ID"
    logo_text: str = "Emergency Health ID"
