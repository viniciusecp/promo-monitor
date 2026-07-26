from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AuthCodeRequest(BaseModel):
    code: str = Field(min_length=4, max_length=8)


class AuthPasswordRequest(BaseModel):
    password: str = Field(min_length=1, max_length=256)


class AuthUser(BaseModel):
    id: int
    first_name: str | None = None
    username: str | None = None


class AuthStatusResponse(BaseModel):
    status: Literal[
        "connecting",
        "unauthenticated",
        "awaiting_code",
        "awaiting_password",
        "authenticated",
        "error",
    ]
    connected: bool
    phone_masked: str
    worker_running: bool
    user: AuthUser | None = None
    error_code: str | None = None
    error_message: str | None = None
    retry_after_seconds: int | None = None
    code_sent_at: datetime | None = None
    can_request_code: bool
