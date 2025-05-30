from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

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
    role: UserRoleInput = UserRoleInput.FAMILY_MEMBER
    date_of_birth: Optional[datetime] = None  # Added date_of_birth field

    # New optional fields to support family linking
    primary_holder_id: Optional[int] = None  # ID of the existing user to link to
    relationship_type: Optional[str] = "dependent"
    sharing_preferences: Optional[dict] = {
        "share_medical": True,
        "share_activity": False
    }

    class Config:
        use_enum_values = True

class UserResponse(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    role: UserRoleInput  # Use DB enum for consistent output
    date_of_birth: Optional[datetime] = None  # Added date_of_birth field
    subscription_id: Optional[int] = None
    stripe_customer_id: Optional[str] = None

    class Config:
        from_attributes = True


class UserWithRoles(UserResponse):
    roles: List[str] = []


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRoleInput] = None  # Use input enum
    subscription_id: Optional[int] = None
    date_of_birth: Optional[datetime] = None  # Added date_of_birth field

    class Config:
        use_enum_values = True
