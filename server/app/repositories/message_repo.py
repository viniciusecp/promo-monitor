from sqlalchemy.orm import Session

from app.models.telegram_message import TelegramMessage
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[TelegramMessage]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, TelegramMessage)

    def exists_by_telegram_id(self, message_id: int, chat_id: int) -> bool:
        from sqlalchemy import select

        query = select(TelegramMessage).where(
            TelegramMessage.message_id == message_id,
            TelegramMessage.chat_id == chat_id,
        )
        return self.db.scalar(query) is not None
