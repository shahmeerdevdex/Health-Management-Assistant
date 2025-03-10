from pydantic import BaseModel,Field
from datetime import datetime,timezone
from typing import Optional

class HealthDiaryCreate(BaseModel):
    symptoms: str
    mood: str
    notes: str
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: int

class HealthDiaryResponse(BaseModel):
    id: int
    user_id: int
    symptoms: str
    mood: str
    notes: str
    date: datetime

    class Config:
        orm_mode = True

class HealthDiaryUpdate(BaseModel):
    symptoms: Optional[str] = None
    mood: Optional[str] = None
    notes: Optional[str] = None
