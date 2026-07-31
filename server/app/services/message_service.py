import re
from dataclasses import dataclass
from datetime import datetime

from app.core.links import build_message_link
from app.core.logging import logger
from app.models.product_interest import ProductInterest
from app.models.telegram_message import TelegramMessage
from app.repositories.match_repo import MatchRepository
from app.repositories.message_repo import MessageRepository
from app.services.alert_service import AlertService
from app.services.llm_validator_service import LLMValidator
from app.services.matcher_service import composite_matcher


URL_PATTERN = re.compile(r"https?://\S+")


@dataclass
class MatchCandidate:
    interest: ProductInterest
    score: float
    preco: float | None
    breakdown: dict[str, float]
    matched_keyword: str | None
    motivo: str | None
    aprovado: bool
    validado: bool
    preco_ok: bool


def extract_links(text: str | None) -> list[str]:
    if not text:
        return []
    return URL_PATTERN.findall(text)


class MessageService:
    def __init__(
        self,
        message_repo: MessageRepository,
        match_repo: MatchRepository,
        alert_service: AlertService,
        llm_validator: LLMValidator,
        interests: list[ProductInterest],
    ) -> None:
        self.message_repo = message_repo
        self.match_repo = match_repo
        self.alert_service = alert_service
        self.llm_validator = llm_validator
        self.interests = interests

    def refresh_interests(self, interests: list[ProductInterest]) -> None:
        self.interests = interests

    async def process_message(
        self,
        message_id: int,
        chat_id: int,
        chat_name: str | None,
        sender_id: int | None,
        sender_name: str | None,
        text: str | None,
        raw_date: datetime | None,
    ) -> None:
        if not text:
            return

        if self.message_repo.exists_by_telegram_id(message_id, chat_id):
            return

        candidates: list[MatchCandidate] = []
        for interest in self.interests:
            if not interest.ativo:
                continue

            score, prices, breakdown, matched_keyword = composite_matcher.match(text, interest)

            if score < 0.6:
                continue

            preco = min(prices) if prices else None
            preco_ok = not (interest.preco_maximo and preco and preco > interest.preco_maximo)

            if not preco_ok:
                logger.debug(
                    "price_above_max",
                    produto=interest.nome_produto,
                    preco=preco,
                    max=interest.preco_maximo,
                )
                candidates.append(
                    MatchCandidate(
                        interest=interest,
                        score=score,
                        preco=preco,
                        breakdown=breakdown,
                        matched_keyword=matched_keyword,
                        motivo=None,
                        aprovado=False,
                        validado=False,
                        preco_ok=False,
                    )
                )
                continue

            ok, motivo, validado = await self.llm_validator.validate(text, interest)
            if not ok:
                logger.info(
                    "llm_rejected",
                    produto=interest.nome_produto,
                    motivo=motivo,
                    chat=chat_name,
                )

            candidates.append(
                MatchCandidate(
                    interest=interest,
                    score=score,
                    preco=preco,
                    breakdown=breakdown,
                    matched_keyword=matched_keyword,
                    motivo=motivo,
                    aprovado=ok,
                    validado=validado,
                    preco_ok=True,
                )
            )

        if not candidates:
            return

        links = extract_links(text)
        msg = self.message_repo.create(
            message_id=message_id,
            chat_id=chat_id,
            chat_name=chat_name,
            sender_id=sender_id,
            sender_name=sender_name,
            text=text,
            links=links,
            raw_date=raw_date,
        )

        for cand in candidates:
            interest = cand.interest
            if self.match_repo.exists_by_message_and_interest(msg.id, interest.id):
                continue

            match = self.match_repo.create(
                message_id=msg.id,
                interest_id=interest.id,
                preco_encontrado=cand.preco,
                score=cand.score,
                raw_text_snippet=text[:300],
                matched_keyword=cand.matched_keyword,
                llm_motivo=cand.motivo,
                llm_aprovado=cand.aprovado,
                llm_validado=cand.validado,
                preco_ok=cand.preco_ok,
            )

            logger.info(
                "match_found",
                produto=interest.nome_produto,
                score=cand.score,
                keyword_score=cand.breakdown.get("keyword"),
                fuzzy_score=cand.breakdown.get("fuzzy"),
                preco=cand.preco,
                chat=chat_name,
                aprovado=cand.aprovado,
                preco_ok=cand.preco_ok,
            )

            if not (cand.preco_ok and cand.aprovado):
                continue

            sent = await self.alert_service.send_alert(
                produto=interest.nome_produto,
                preco=f"R$ {cand.preco:.2f}" if cand.preco else "Não informado",
                link=build_message_link(chat_id, message_id),
                chat_id=chat_id,
                message_id=message_id,
                texto=text,
            )
            if sent:
                self.match_repo.mark_alerted(match.id)
