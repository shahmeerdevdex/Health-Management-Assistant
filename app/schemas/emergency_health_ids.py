from pydantic import BaseModel
from typing import Optional

class EmergencyHealthIDCreate(BaseModel):
    allergies: Optional[str] = None
    medications: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    critical_conditions: Optional[str] = None

class EmergencyHealthIDResponse(EmergencyHealthIDCreate):
    id: int
    user_id: int

    class Config:
        orm_mode = True
