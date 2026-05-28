from sqlalchemy.orm import Session

from app.models.promotion_match import PromotionMatch
from app.repositories.base import BaseRepository


class MatchRepository(BaseRepository[PromotionMatch]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, PromotionMatch)

    def exists_by_message_and_interest(self, message_id: int, interest_id: int) -> bool:
        from sqlalchemy import select

        query = select(PromotionMatch).where(
            PromotionMatch.message_id == message_id,
            PromotionMatch.interest_id == interest_id,
        )
        return self.db.scalar(query) is not None
