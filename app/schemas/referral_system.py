from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SpecialistType(str, Enum):
    CARDIOLOGIST = "CARDIOLOGIST"
    NEUROLOGIST = "NEUROLOGIST"
    DERMATOLOGIST = "DERMATOLOGIST"
    ORTHOPEDIST = "ORTHOPEDIST"
    PEDIATRICIAN = "PEDIATRICIAN"
    PSYCHIATRIST = "PSYCHIATRIST"
    # Add more specialist types as needed


class ReferralStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class ReferralPriority(str, Enum):
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    EMERGENCY = "EMERGENCY"


# Shared base schema
class ReferralBase(BaseModel):
    patient_id: int = Field(..., description="ID of the patient being referred")
    from_practitioner_id: int = Field(..., description="ID of the referring practitioner")
    to_practitioner_id: int = Field(..., description="ID of the receiving practitioner")
    specialist_type: SpecialistType = Field(..., description="Type of specialist being referred to")
    reason: str = Field(..., description="Reason for referral")
    priority: ReferralPriority = Field(default=ReferralPriority.ROUTINE, description="Priority level of the referral")
    notes: Optional[str] = Field(None, description="Additional notes about the referral")
    required_tests: Optional[List[str]] = Field(None, description="Required tests or documents")
    appointment_preferred_dates: Optional[List[datetime]] = Field(None, description="Preferred appointment dates")
    medical_history_required: bool = Field(default=True, description="Whether medical history is required")
    test_results_required: bool = Field(default=True, description="Whether test results are required")


# Schema for creating a referral
class ReferralCreate(ReferralBase):
    pass


# Schema for updating a referral status or notes
class ReferralUpdate(BaseModel):
    status: Optional[ReferralStatus] = Field(None, description="Updated status of the referral")
    notes: Optional[str] = Field(None, description="Additional notes")
    appointment_date: Optional[datetime] = Field(None, description="Scheduled appointment date")
    feedback: Optional[str] = Field(None, description="Feedback from the receiving practitioner")
    documents_attached: Optional[List[str]] = Field(None, description="List of attached document IDs")


# Schema for returning referral data in responses
class ReferralResponse(ReferralBase):
    id: int
    status: ReferralStatus
    created_at: datetime
    updated_at: datetime
    appointment_date: Optional[datetime]
    feedback: Optional[str]
    documents_attached: Optional[List[str]]
    workflow_history: List[Dict[str, Any]] = Field(default_factory=list, description="History of status changes and actions")

    class Config:
        from_attributes = True
