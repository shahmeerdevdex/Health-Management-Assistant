from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MedicationCreate(BaseModel):
    user_id: int 
    name: str
    dosage: str
    frequency: str
    start_date: datetime
    end_date: datetime

class MedicationResponse(BaseModel):
    id: int
    user_id: int
    name: str
    dosage: str
    frequency: str
    start_date: datetime
    end_date: datetime

    class Config:
        orm_mode = True


class MedicationUpdate(BaseModel):
    name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
