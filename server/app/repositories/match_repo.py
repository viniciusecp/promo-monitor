from datetime import datetime, timezone

from sqlalchemy import Row, Select, and_, asc, desc, func, or_, select, update
from sqlalchemy.orm import Session

from app.core.timeutils import utcnow_naive
from app.models.product_interest import ProductInterest
from app.models.promotion_match import PromotionMatch
from app.models.telegram_message import TelegramMessage
from app.repositories.base import BaseRepository
from app.schemas.match import (
    MatchFilterParams,
    MatchOrderBy,
    MatchOrderDir,
    MatchStatus,
)

_ORDER_COLUMNS = {
    MatchOrderBy.data: PromotionMatch.created_at,
    MatchOrderBy.preco: PromotionMatch.preco_encontrado,
    MatchOrderBy.score: PromotionMatch.score,
}


def _where_clauses(filters: MatchFilterParams, since: datetime | None) -> list:
    """Cláusulas WHERE compartilhadas por list, count e mark_all_read.

    Ter uma origem só é o que garante que "marcar todos como lidos" atinja
    exatamente o conjunto que o usuário está vendo.
    """
    clauses = []

    if since is not None:
        clauses.append(PromotionMatch.created_at >= since)

    if filters.nao_lidos:
        clauses.append(PromotionMatch.lido.is_(False))

    if filters.status:
        status_or = []
        if MatchStatus.alertado in filters.status:
            status_or.append(PromotionMatch.alerted.is_(True))
        if MatchStatus.reprovado in filters.status:
            status_or.append(
                and_(
                    PromotionMatch.llm_validado.is_(True),
                    PromotionMatch.llm_aprovado.is_(False),
                )
            )
        clauses.append(or_(*status_or))

    if filters.chat_id is not None:
        clauses.append(TelegramMessage.chat_id == filters.chat_id)

    if filters.preco_min is not None:
        clauses.append(PromotionMatch.preco_encontrado >= filters.preco_min)

    if filters.preco_max is not None:
        clauses.append(PromotionMatch.preco_encontrado <= filters.preco_max)

    return clauses


class MatchRepository(BaseRepository[PromotionMatch]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, PromotionMatch)

    def mark_alerted(self, match_id: int) -> None:
        self.update(
            match_id,
            alerted=True,
            alerted_at=datetime.now(timezone.utc),
        )

    def set_lido(self, match_id: int, lido: bool) -> PromotionMatch | None:
        return self.update(
            match_id,
            lido=lido,
            lido_em=utcnow_naive() if lido else None,
        )

    def exists_by_message_and_interest(self, message_id: int, interest_id: int) -> bool:
        query = select(PromotionMatch).where(
            PromotionMatch.message_id == message_id,
            PromotionMatch.interest_id == interest_id,
        )
        return self.db.scalar(query) is not None

    # -- feed -------------------------------------------------------------

    def _base_join(self, stmt: Select) -> Select:
        return stmt.join(
            TelegramMessage, PromotionMatch.message_id == TelegramMessage.id
        ).join(ProductInterest, PromotionMatch.interest_id == ProductInterest.id)

    def list_detailed(
        self,
        filters: MatchFilterParams,
        since: datetime | None,
        skip: int,
        limit: int,
    ) -> list[Row]:
        column = _ORDER_COLUMNS[filters.order_by]
        direction = asc if filters.order_dir is MatchOrderDir.asc else desc

        stmt = self._base_join(
            select(
                PromotionMatch,
                TelegramMessage.chat_name,
                TelegramMessage.text,
                TelegramMessage.chat_id,
                TelegramMessage.message_id,
                ProductInterest.nome_produto,
            )
        ).where(*_where_clauses(filters, since))

        stmt = stmt.order_by(direction(column), desc(PromotionMatch.id))

        return list(self.db.execute(stmt.offset(skip).limit(limit)).all())

    def count_detailed(
        self, filters: MatchFilterParams, since: datetime | None
    ) -> int:
        stmt = self._base_join(select(func.count(PromotionMatch.id)))
        return self.db.scalar(stmt.where(*_where_clauses(filters, since))) or 0

    def mark_all_read(
        self, filters: MatchFilterParams, since: datetime | None
    ) -> int:
        ids = list(
            self.db.scalars(
                self._base_join(select(PromotionMatch.id)).where(
                    *_where_clauses(filters, since),
                    PromotionMatch.lido.is_(False),
                )
            ).all()
        )
        if not ids:
            return 0

        self.db.execute(
            update(PromotionMatch)
            .where(PromotionMatch.id.in_(ids))
            .values(lido=True, lido_em=utcnow_naive())
        )
        self.db.commit()
        return len(ids)

    # -- agregados --------------------------------------------------------

    def distinct_chats(self) -> list[Row]:
        stmt = (
            select(
                TelegramMessage.chat_id,
                func.max(TelegramMessage.chat_name),
                func.count(PromotionMatch.id),
            )
            .join(TelegramMessage, PromotionMatch.message_id == TelegramMessage.id)
            .group_by(TelegramMessage.chat_id)
            .order_by(desc(func.count(PromotionMatch.id)))
        )
        return list(self.db.execute(stmt).all())
