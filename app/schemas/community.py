from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

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
    created_at: Optional[datetime]  
    is_anonymous: bool

class CommunityCommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    content: str
    created_at: Optional[datetime]  

class CommunityLikeRequest(BaseModel):
    post_id: int
    message: str
    
class CommunityReportRequest(BaseModel):
    reason: str

class CommunityCommentRequest(BaseModel):
    content: str    
    
class SupportGroupBase(BaseModel):
    name: str
    condition_tag: str
    description: Optional[str] = None

class SupportGroupCreate(SupportGroupBase):
    pass

class SupportGroupResponse(SupportGroupBase):
    id: int

    class Config:
        orm_mode = True

class GroupPostCreate(BaseModel):
    title: str
    content: str
    is_anonymous: Optional[bool] = False
    