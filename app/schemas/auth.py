from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    """Schema for user login request."""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str
