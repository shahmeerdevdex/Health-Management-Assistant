from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List

class MessageCreate(BaseModel):
    receiver_id: int
    content: str
    message_type: str = Field(default="general", description="Type of message (general, medical, sensitive)")
    retention_period: Optional[int] = Field(default=365, description="Days to retain the message")
    meta_data: Optional[Dict[str, Any]] = Field(default=None, description="Additional message metadata")

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    timestamp: datetime
    is_read: bool
    message_type: str
    retention_period: int
    is_encrypted: bool
    deleted_at: Optional[datetime] = None
    meta_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class MessageAuditLogCreate(BaseModel):
    message_id: int
    action: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None

class MessageAuditLogResponse(BaseModel):
    id: int
    message_id: int
    user_id: int
    action: str
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
