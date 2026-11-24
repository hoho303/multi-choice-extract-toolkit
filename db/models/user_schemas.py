from datetime import datetime
from .base import BaseSchema
from pydantic import Field

# Models
class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserRegisterRequest(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=3)
    
class UserLoginRequest(BaseSchema):
    username: str
    password: str

class UserResponse(BaseSchema):
    id: int
    username: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenVerifyRequest(BaseSchema):
    token: str

class TokenRefreshRequest(BaseSchema):
    refresh_token: str