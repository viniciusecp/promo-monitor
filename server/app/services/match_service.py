# Adiado porque o método `list` sombreia o builtin `list` dentro do corpo da
# classe, quebrando anotações como `list[MatchChatResponse]`.
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.exceptions import MatchNotFoundError
from app.core.links import build_message_link
from app.core.timeutils import resolve_timezone
from app.models.product_interest import ProductInterest
from app.models.promotion_match import PromotionMatch
from app.repositories.interest_repo import InterestRepository
from app.repositories.match_repo import MatchRepository
from app.schemas.match import (
    MatchChatResponse,
    MatchDetailResponse,
    MatchFilterParams,
    MatchListResponse,
    MatchPeriod,
    MatchReadResponse,
    MatchStatsResponse,
)


def resolve_period_start(periodo: MatchPeriod, tz_name: str | None) -> datetime | None:
    """Início do período, como datetime **naive em UTC**.

    Precisa ser naive-UTC porque é assim que `created_at` está gravado — ver
    `app.core.timeutils`. Comparar com um datetime aware em -03:00 compararia
    21:00 com 00:00 e a janela sairia deslocada em 3 horas.

    `hoje` é fronteira de calendário no fuso do **usuário**: sem o round-trip de
    fuso, às 20h de Brasília "hoje" começaria à meia-noite UTC, que é 21h do dia
    anterior em BRT — e o filtro incluiria 3 horas do dia errado. `7d` e `30d`
    são janelas móveis e não dependem de fuso nenhum.
    """
    if periodo is MatchPeriod.tudo:
        return None

    now_utc = datetime.now(timezone.utc)

    if periodo is MatchPeriod.hoje:
        local_midnight = now_utc.astimezone(resolve_timezone(tz_name)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        start = local_midnight.astimezone(timezone.utc)
    elif periodo is MatchPeriod.d7:
        start = now_utc - timedelta(days=7)
    else:
        start = now_utc - timedelta(days=30)

    return start.replace(tzinfo=None)


class MatchService:
    def __init__(
        self,
        match_repo: MatchRepository,
        interest_repo: InterestRepository,
    ) -> None:
        self.match_repo = match_repo
        self.interest_repo = interest_repo

    def list(
        self, filters: MatchFilterParams, skip: int, limit: int
    ) -> MatchListResponse:
        since = resolve_period_start(filters.periodo, filters.tz)

        rows = self.match_repo.list_detailed(filters, since, skip=skip, limit=limit)
        total = self.match_repo.count_detailed(filters, since)

        items = [
            self._to_detail(
                match,
                chat_name=chat_name,
                message_text=text,
                chat_id=chat_id,
                telegram_message_id=telegram_message_id,
                produto_nome=produto_nome,
            )
            for (
                match,
                chat_name,
                text,
                chat_id,
                telegram_message_id,
                produto_nome,
            ) in rows
        ]

        return MatchListResponse(
            items=items,
            total=total,
            has_more=skip + len(items) < total,
        )

    def set_lido(self, match_id: int, lido: bool) -> MatchReadResponse:
        match = self.match_repo.set_lido(match_id, lido)
        if match is None:
            raise MatchNotFoundError(match_id)
        return MatchReadResponse(id=match.id, lido=match.lido, lido_em=match.lido_em)

    def mark_all_read(self, filters: MatchFilterParams) -> int:
        since = resolve_period_start(filters.periodo, filters.tz)
        return self.match_repo.mark_all_read(filters, since)

    def stats(self, tz_name: str | None) -> MatchStatsResponse:
        now_utc = datetime.now(timezone.utc)
        inicio_hoje = resolve_period_start(MatchPeriod.hoje, tz_name)
        ha_24h = (now_utc - timedelta(hours=24)).replace(tzinfo=None)
        ha_7d = (now_utc - timedelta(days=7)).replace(tzinfo=None)

        return MatchStatsResponse(
            nao_lidos=self.match_repo.count_where(PromotionMatch.lido.is_(False)),
            novos_hoje=self.match_repo.count_where(
                PromotionMatch.created_at >= inicio_hoje
            ),
            ultimas_24h=self.match_repo.count_where(
                PromotionMatch.created_at >= ha_24h
            ),
            ultimos_7d=self.match_repo.count_where(PromotionMatch.created_at >= ha_7d),
            interesses_ativos=self.interest_repo.count_where(
                ProductInterest.ativo.is_(True)
            ),
        )

    def chats(self) -> list[MatchChatResponse]:
        return [
            MatchChatResponse(chat_id=chat_id, chat_name=chat_name, total=total)
            for chat_id, chat_name, total in self.match_repo.distinct_chats()
        ]

    def _to_detail(
        self,
        match: PromotionMatch,
        *,
        chat_name: str | None,
        message_text: str | None,
        chat_id: int | None,
        telegram_message_id: int | None,
        produto_nome: str,
    ) -> MatchDetailResponse:
        link = ""
        if chat_id and telegram_message_id:
            link = build_message_link(chat_id, telegram_message_id)

        return MatchDetailResponse(
            **{
                column: getattr(match, column)
                for column in (
                    "id",
                    "message_id",
                    "interest_id",
                    "preco_encontrado",
                    "score",
                    "raw_text_snippet",
                    "matched_keyword",
                    "llm_motivo",
                    "llm_aprovado",
                    "llm_validado",
                    "preco_ok",
                    "alerted",
                    "alerted_at",
                    "lido",
                    "lido_em",
                    "created_at",
                )
            },
            chat_name=chat_name,
            message_text=message_text,
            message_link=link,
            produto_nome=produto_nome,
        )
