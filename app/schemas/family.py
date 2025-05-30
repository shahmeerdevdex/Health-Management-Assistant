from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class FamilyLinkCreate(BaseModel):
    family_member_id: int
    relationship_type: str
    sharing_preferences: Optional[Dict[str, Any]] = None


class FamilyLinkResponse(BaseModel):
    id: int
    user_id: int
    family_member_id: int
    relationship_type: str
    sharing_preferences: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # replaces orm_mode in Pydantic v2


class FamilyMemberResponse(BaseModel):
    user_id: int
    name: str
    relationship_type: str
    sharing_preferences: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class FamilyHealthSummaryResponse(BaseModel):
    id: int
    family_id: int
    generated_at: datetime
    last_updated: datetime
    overall_health_status: str
    medications: List[Dict[str, Any]]
    upcoming_appointments: List[Dict[str, Any]]
    recent_health_events: List[Dict[str, Any]]
    notes: Optional[str] = None

    class Config:
        from_attributes = True
