from sqlalchemy.orm import Session

from app.models.telegram_message import TelegramMessage
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[TelegramMessage]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, TelegramMessage)

    def exists_by_telegram_id(self, message_id: int, chat_id: int) -> bool:
        from sqlalchemy import select

        query = (
            select(TelegramMessage.id)
            .where(
                TelegramMessage.chat_id == chat_id,
                TelegramMessage.message_id == message_id,
            )
            .limit(1)
        )
        return self.db.scalar(query) is not None

    def list_recent(self, limit: int = 500) -> list[TelegramMessage]:
        from sqlalchemy import select

        query = (
            select(TelegramMessage)
            .order_by(TelegramMessage.id.desc())
            .limit(limit)
        )
        return list(self.db.scalars(query).all())
