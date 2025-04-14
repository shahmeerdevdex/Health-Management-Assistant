from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class ReferralStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


# Shared base schema
class ReferralBase(BaseModel):
    patient_id: int = Field(..., description="ID of the patient being referred")
    from_practitioner_id: int = Field(..., description="ID of the referring practitioner")
    to_practitioner_id: int = Field(..., description="ID of the receiving practitioner")
    reason: str = Field(..., description="Reason for referral")
    notes: Optional[str] = Field(None, description="Additional notes about the referral")


# Schema for creating a referral
class ReferralCreate(ReferralBase):
    pass


# Schema for updating a referral status or notes
class ReferralUpdate(BaseModel):
    status: Optional[ReferralStatus] = Field(None, description="Updated status of the referral")
    notes: Optional[str] = Field(None, description="Additional notes")


# Schema for returning referral data in responses
class ReferralResponse(ReferralBase):
    id: int
    status: ReferralStatus
    created_at: datetime

    class Config:
        orm_mode = True
