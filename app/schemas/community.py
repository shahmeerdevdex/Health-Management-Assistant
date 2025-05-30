from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.models.community import ModerationStatus, ReportSeverity

class CommunityPostRequest(BaseModel):
    title: str
    content: str
    category: str
    is_anonymous: bool = False

class CommunityPostResponse(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    category: str
    created_at: datetime
    is_anonymous: bool
    status: ModerationStatus
    moderation_notes: Optional[str] = None
    moderated_at: Optional[datetime] = None
    last_edited_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CommunityCommentRequest(BaseModel):
    content: str
    parent_comment_id: Optional[int] = None

class CommunityCommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    content: str
    created_at: datetime
    status: ModerationStatus
    moderation_notes: Optional[str] = None
    moderated_at: Optional[datetime] = None
    parent_comment_id: Optional[int] = None

    class Config:
        from_attributes = True

class CommunityLikeRequest(BaseModel):
    post_id: int
    message: str

class CommunityReportRequest(BaseModel):
    reason: str
    severity: ReportSeverity = ReportSeverity.MEDIUM

class ModerationActionRequest(BaseModel):
    action: ModerationStatus
    notes: Optional[str] = None

class ModerationResponse(BaseModel):
    id: int
    status: ModerationStatus
    message: str

class SupportGroupBase(BaseModel):
    name: str
    condition_tag: str
    description: Optional[str] = None
    is_private: bool = False
    requires_approval: bool = False
    rules: Optional[str] = None

class SupportGroupCreate(SupportGroupBase):
    pass

class SupportGroupResponse(SupportGroupBase):
    id: int
    created_at: datetime
    member_count: int
    moderator_ids: Optional[str] = None

    class Config:
        from_attributes = True

class GroupPostCreate(BaseModel):
    title: str
    content: str
    is_anonymous: Optional[bool] = False

class GroupMembershipRequest(BaseModel):
    group_id: int
    role: str = "member"  # member, moderator, admin

class GroupMembershipResponse(BaseModel):
    id: int
    group_id: int
    user_id: int
    role: str
    joined_at: datetime
    status: str

    class Config:
        from_attributes = True

class CommunityReportResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    reason: str
    severity: ReportSeverity
    created_at: datetime
    status: str
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    class Config:
        from_attributes = True
    