from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str  

class UserResponse(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool  
    created_at: datetime  

    class Config:
        orm_mode = True  
class UserWithRoles(UserResponse):
    roles: List[str] = []

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
