from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Already existing
class PractitionerCreate(BaseModel):
    name: str
    specialty: str
    contact_info: str

class PractitionerResponse(BaseModel):
    id: int
    name: str
    specialty: str
    contact_info: str

    class Config:
        from_attributes = True

# NEW: Patient Summary used in /dashboard
class PatientSummary(BaseModel):
    id: int
    full_name: str
    email: str
    latest_diary_entry: Optional[str] = None
    active_medications: List[str] = []
    alerts: Optional[List[str]] = []

    class Config:
        from_attributes = True
