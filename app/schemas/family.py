from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FamilyLinkCreate(BaseModel):
    family_member_id: int
    relation_type: str
    permission: Optional[str] = "read"


class FamilyLinkResponse(BaseModel):
    id: int
    user_id: int
    family_member_id: int
    relation_type: str
    permission: str
    created_at: datetime

    class Config:
        from_attributes = True  # replaces orm_mode in Pydantic v2
