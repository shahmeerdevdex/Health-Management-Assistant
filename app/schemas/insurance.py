from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

from enum import Enum

class VerificationStatusEnum(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

    @classmethod
    def _missing_(cls, value):
        # Handles lowercase input like "verified", "rejected"
        if isinstance(value, str):
            value = value.upper()
            if value in cls.__members__:
                return cls[value]
        return super()._missing_(value)


class InsuranceCreate(BaseModel):
    provider_name: str
    policy_number: str
    coverage_start: date
    coverage_end: date
    deductible: Optional[int] = None
    premium_amount: Optional[int] = None

class InsuranceResponse(BaseModel):
    id: int
    user_id: int
    provider_name: str
    policy_number: str
    coverage_start: date
    coverage_end: date
    deductible: Optional[int]
    premium_amount: Optional[int]

    # Extended fields based on client requirements
    is_verified: Optional[bool] = None
    verification_status: Optional[VerificationStatusEnum] = None
    verified_at: Optional[datetime] = None
    card_url: Optional[str] = None  # URL to Apple/Google wallet-compatible health card

    class Config:
        orm_mode = True