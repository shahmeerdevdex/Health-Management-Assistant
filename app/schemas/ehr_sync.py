from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class MedicalHistoryEntry(BaseModel):
    condition: str
    diagnosed_on: date

class EHRSyncRequest(BaseModel):
    user_id: int
    medical_history: List[MedicalHistoryEntry]

class EHRSyncResponse(BaseModel):
    ehr_id: str
    medical_history: List[MedicalHistoryEntry]
    last_updated: date

    class Config:
        orm_mode = True
