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
        from_attributes = True

class OutOfPocketCostCreate(BaseModel):
    insurance_plan_id: int
    amount: int
    date: date
    description: Optional[str] = None

class OutOfPocketCostResponse(BaseModel):
    id: int
    insurance_plan_id: int
    amount: int
    date: date
    description: Optional[str] = None

    class Config:
        from_attributes = True

class MedicareClaimCreate(BaseModel):
    insurance_plan_id: int
    claim_id: str
    claim_date: date
    claim_amount: int

class MedicareClaimResponse(BaseModel):
    id: int
    insurance_plan_id: int
    claim_id: str
    claim_date: date
    claim_amount: int

    class Config:
        from_attributes = True

class InsuranceCoverageDetailCreate(BaseModel):
    insurance_plan_id: int
    coverage_type: str
    benefits: Optional[str] = None
    exclusions: Optional[str] = None

class InsuranceCoverageDetailResponse(BaseModel):
    id: int
    insurance_plan_id: int
    coverage_type: str
    benefits: Optional[str] = None
    exclusions: Optional[str] = None

    class Config:
        from_attributes = True