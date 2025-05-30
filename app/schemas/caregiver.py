from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CaregiverRequest(BaseModel):
    user_id: int  # The caregiver's user ID
    patient_id: int  # The patient under care
    tasks: List[str]  # Tasks assigned to the caregiver (e.g., medication reminders, appointments)
    schedule: Optional[str] = None  # Caregiving schedule details
    emergency_contact: Optional[str] = None  # Emergency contact information
    appointment_history: Optional[List[dict]] = None  # Past and upcoming appointments
    medication_tracking: Optional[List[dict]] = None  # Medication updates for dependents
    monitoring_data: Optional[List[dict]] = None  # Health monitoring data
    financial_support: Optional[dict] = None  # Financial details (NDIS, insurance)

class CaregiverResponse(BaseModel):
    user_id: int
    patient_id: int
    assigned_tasks: List[str]  # List of tasks confirmed
    appointment_history: Optional[List[dict]] = None  # Past and upcoming appointments
    medication_tracking: Optional[List[dict]] = None  # Medication updates
    monitoring_data: Optional[List[dict]] = None  # Health monitoring data
    financial_support: Optional[dict] = None  # Financial management details
    message: str  # Confirmation or feedback message


class CaregiverAssignmentResponse(BaseModel):
    id: int
    caregiver_id: int
    patient_id: int
    tasks: List[str]
    schedule: Optional[str] = None
    emergency_contact: Optional[str] = None
    assigned_at: Optional[datetime] = None

    class Config:
        from_attributes = True  
        
class CaregiverProfileResponse(BaseModel):
    user_id: int
    name: Optional[str]
    phone: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
        