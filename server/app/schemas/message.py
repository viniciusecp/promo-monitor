from datetime import datetime

from pydantic import BaseModel


class MessageResponse(BaseModel):
    id: int
    message_id: int
    chat_id: int
    chat_name: str | None
    sender_id: int | None
    sender_name: str | None
    text: str | None
    links: list[str] | None
    raw_date: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
