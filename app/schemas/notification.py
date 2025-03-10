from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NotificationCreate(BaseModel):
    message: str

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    message: str
    sent_at: datetime

    class Config:
        orm_mode = True

class NotificationCreate(BaseModel):
    title: str
    message: str
    user_id: int

class NotificationUpdate(BaseModel): 
    title: Optional[str] = None
    message: Optional[str] = None
