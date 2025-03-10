from pydantic import BaseModel
from datetime import datetime

class MedicationLogCreate(BaseModel):
    medication_id: int
    taken_at: datetime

class MedicationLogResponse(BaseModel):
    id: int
    user_id: int
    medication_id: int
    taken_at: datetime

    class Config:
        orm_mode = True
