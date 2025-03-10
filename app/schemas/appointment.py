from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AppointmentCreate(BaseModel):
    doctor_name: str
    date: datetime
    location: str

class AppointmentResponse(BaseModel):
    id: int
    user_id: int
    doctor_name: str
    date: datetime
    location: str

    class Config:
        orm_mode = True


class AppointmentUpdate(BaseModel):
    doctor_name: Optional[str] = None
    date: Optional[datetime] = None
    location: Optional[str] = None
