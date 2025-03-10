from pydantic import BaseModel
from datetime import datetime

class SymptomAnalysisCreate(BaseModel):
    symptoms: str

class SymptomAnalysisResponse(BaseModel):
    id: int
    user_id: int
    symptoms: str
    analysis_result: str
    generated_at: datetime

    class Config:
        orm_mode = True
