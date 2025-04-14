from pydantic import BaseModel
from app.db.models.user import UserRoleEnum

class RoleResponse(BaseModel):
    user_id: int
    role: UserRoleEnum

class RoleUpdateRequest(BaseModel):
    user_id: int  # The user whose role is being updated
    new_role: UserRoleEnum
