from pydantic import BaseModel
from datetime import datetime

class HealthTipCreate(BaseModel):
    tip: str

class HealthTipResponse(BaseModel):
    id: int
    user_id: int
    tip: str
    generated_at: datetime

    class Config:
        orm_mode = True
