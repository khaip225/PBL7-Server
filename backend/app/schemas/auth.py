from uuid import UUID
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: UUID
    username: str
    display_name: str
    is_active: bool

    model_config = {"from_attributes": True}
