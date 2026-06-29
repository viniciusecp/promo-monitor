from datetime import datetime

from pydantic import BaseModel, Field


class InterestCreate(BaseModel):
    nome_produto: str = Field(..., min_length=1, max_length=255)
    preco_maximo: float | None = Field(None, ge=0)
    limiar_match: float | None = Field(None, ge=0, le=1)
    palavras_chave: list[str] = Field(default_factory=list)
    palavras_excluidas: list[str] = Field(default_factory=list)
    ativo: bool = True


class InterestUpdate(BaseModel):
    nome_produto: str | None = Field(None, min_length=1, max_length=255)
    preco_maximo: float | None = None
    limiar_match: float | None = Field(None, ge=0, le=1)
    palavras_chave: list[str] | None = None
    palavras_excluidas: list[str] | None = None
    ativo: bool | None = None


class InterestResponse(BaseModel):
    id: int
    nome_produto: str
    preco_maximo: float | None
    limiar_match: float | None
    palavras_chave: list[str]
    palavras_excluidas: list[str]
    ativo: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
