from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1, max_length=200)


class ChangePasswordRequest(BaseModel):
    senha_atual: str = Field(min_length=1, max_length=200)
    senha_nova: str = Field(min_length=1, max_length=200)


class SessionResponse(BaseModel):
    user: UserResponse


class LogoutResponse(BaseModel):
    ok: bool = True
