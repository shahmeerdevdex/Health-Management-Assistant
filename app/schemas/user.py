from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional
from app.db.models.user import UserRoleEnum  # Used for response only


# Case-insensitive Enum for input validation
from enum import Enum

class UserRoleInput(str, Enum):
    ADMIN = "ADMIN"
    PRIMARY_HOLDER = "PRIMARY_HOLDER"
    FAMILY_MEMBER = "FAMILY_MEMBER"
    PRACTITIONER = "PRACTITIONER"
    CAREGIVER = "CAREGIVER" 
    PROFESSIONAL = "PROFESSIONAL"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            normalized = value.strip().upper()
            for member in cls:
                if member.value == normalized:
                    return member
        return None


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRoleInput = UserRoleInput.FAMILY_MEMBER  # Use input enum
    subscription_id: Optional[int] = None
    specialty: Optional[str] = None
    contact_info: Optional[str] = None
    phone: Optional[str] = None
    
    location: Optional[str] = None  # For professional
    accepts_insurance: Optional[bool] = False
    online_available: Optional[bool] = True


    class Config:
        use_enum_values = True


class UserResponse(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    role: UserRoleEnum  # Use DB enum for consistent output
    subscription_id: Optional[int] = None
    stripe_customer_id: Optional[str] = None

    class Config:
        orm_mode = True


class UserWithRoles(UserResponse):
    roles: List[str] = []


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRoleInput] = None  # Use input enum
    subscription_id: Optional[int] = None

    class Config:
        use_enum_values = True
