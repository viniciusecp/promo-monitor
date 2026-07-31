from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

Papel = Literal["owner", "viewer"]


class UserResponse(BaseModel):
    """Representação pública — `senha_hash` nunca entra aqui."""

    id: int
    email: str
    nome: str
    papel: Papel
    ativo: bool
    trocar_senha: bool
    ultimo_login: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    nome: str = Field(min_length=1, max_length=120)
    papel: Papel = "viewer"
    senha: str = Field(min_length=1, max_length=200)


class UserUpdate(BaseModel):
    """Atualização parcial: campo ausente significa "não mexe"."""

    nome: str | None = Field(None, min_length=1, max_length=120)
    papel: Papel | None = None
    ativo: bool | None = None


class UserPasswordReset(BaseModel):
    senha: str = Field(min_length=1, max_length=200)
