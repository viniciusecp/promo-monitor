from datetime import datetime

from pydantic import BaseModel


class MatchResponse(BaseModel):
    id: int
    message_id: int
    interest_id: int
    preco_encontrado: float | None
    score: float
    raw_text_snippet: str | None
    alerted: bool
    alerted_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MatchDetailResponse(MatchResponse):
    chat_name: str | None
    message_text: str | None
    message_link: str | None
    produto_nome: str
