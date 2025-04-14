from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MessageCreate(BaseModel):
    receiver_id: int  
    content: str

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    timestamp: datetime
    is_read: bool

    class Config:
        orm_mode = True
