from pydantic import BaseModel
from app.db.models.user import UserRoleInput

class RoleResponse(BaseModel):
    user_id: int
    role: UserRoleInput

class RoleUpdateRequest(BaseModel):
    user_id: int  # The user whose role is being updated
    new_role: UserRoleInput
