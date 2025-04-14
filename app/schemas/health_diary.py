from pydantic import BaseModel, Field,conint
from datetime import datetime, timezone
from typing import Optional, List

class HealthDiaryCreate(BaseModel):
    symptoms: List[str]  
    mood: int = Field(..., ge=1, le=5, description="Mood must be between 1 and 5")          
    notes: Optional[str] = None
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: int

class HealthDiaryResponse(BaseModel):
    id: int
    user_id: int
    symptoms: List[str]
    mood: int
    notes: Optional[str] = None
    date: datetime

    class Config:
        orm_mode = True

class HealthDiaryUpdate(BaseModel):
    symptoms: Optional[List[str]] = None
    mood: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None
