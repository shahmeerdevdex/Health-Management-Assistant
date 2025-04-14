from pydantic import BaseModel
from datetime import datetime
from typing import List

class SymptomAnalysisCreate(BaseModel):
    symptoms: str

class SymptomAnalysisResponse(BaseModel):
    id: int
    user_id: int
    symptoms: str
    conditions: List[str]  
    urgency_level: str  
    next_steps: str  
    generated_at: datetime

    class Config:
        orm_mode = True
