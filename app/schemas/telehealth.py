from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TelehealthSessionBase(BaseModel):
    """
    Base schema for a telehealth session.
    """
    user_id: int
    practitioner_id: int
    session_status: Optional[str] = "active"  

class TelehealthSessionCreate(TelehealthSessionBase):
    """
    Schema for creating a new telehealth session.
    """
    pass  # Inherits fields from TelehealthSessionBase

class TelehealthSessionResponse(TelehealthSessionBase):
    """
    Schema for returning telehealth session details.
    """
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  
