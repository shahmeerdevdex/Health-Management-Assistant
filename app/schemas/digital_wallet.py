from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class CredentialType(str, Enum):
    SMART_HEALTH_CARD = "smart_health_card"
    MEDICARE_CARD = "medicare_card"
    VACCINATION_RECORD = "vaccination_record"
    MEDICAL_RECORD = "medical_record"
    PRESCRIPTION = "prescription"
    LAB_RESULT = "lab_result"
    EMERGENCY_HEALTH_ID = "emergency_health_id"

class CredentialStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"

class DigitalCredential(BaseModel):
    id: int
    user_id: int
    credential_type: CredentialType
    credential_data: Dict[str, Any]
    status: CredentialStatus
    issued_at: datetime
    expires_at: Optional[datetime] = None
    issuer: str
    verification_status: bool = False
    verification_timestamp: Optional[datetime] = None
    credential_metadata: Optional[Dict[str, Any]] = None

class CredentialShareRequest(BaseModel):
    credential_id: int
    recipient_email: str
    recipient_name: str
    access_duration: Optional[int] = None  # Duration in hours
    purpose: str
    scope: List[str]  # List of allowed actions/access levels

class CredentialVerificationRequest(BaseModel):
    credential_id: int
    verification_method: str
    verification_data: Dict[str, Any]

class SmartHealthCard(BaseModel):
    type: str = "smart_health_card"
    version: str = "1.0"
    issuer: str
    issuance_date: datetime
    expiration_date: Optional[datetime]
    credential_data: Dict[str, Any]
    verification_url: Optional[str]
    qr_code: Optional[str]

class MedicareDigitalCard(BaseModel):
    type: str = "medicare_card"
    medicare_number: str
    beneficiary_name: str
    date_of_birth: str
    gender: str
    coverage_type: str
    effective_date: datetime
    expiration_date: Optional[datetime]
    verification_status: bool = False

class DigitalWalletResponse(BaseModel):
    credentials: List[DigitalCredential]
    total_credentials: int
    active_credentials: int
    expired_credentials: int
    verification_status: Dict[str, int]  # Count of verified vs unverified credentials 