import re
from datetime import datetime

from app.core.config import settings
from app.core.logging import logger
from app.models.product_interest import ProductInterest
from app.models.telegram_message import TelegramMessage
from app.repositories.match_repo import MatchRepository
from app.repositories.message_repo import MessageRepository
from app.services.alert_service import AlertService
from app.services.llm_validator_service import LLMValidator
from app.services.matcher_service import composite_matcher


URL_PATTERN = re.compile(r"https?://\S+")


def extract_links(text: str | None) -> list[str]:
    if not text:
        return []
    return URL_PATTERN.findall(text)


def build_message_link(chat_id: int, message_id: int) -> str:
    chat_id_str = str(chat_id)
    if chat_id_str.startswith("-100"):
        chat_id_str = chat_id_str[4:]
    elif chat_id_str.startswith("-"):
        chat_id_str = chat_id_str[1:]
    return f"https://t.me/c/{chat_id_str}/{message_id}"


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

        # Avalia os interesses ANTES de persistir: só guardamos no banco as
        # mensagens que realmente geram match. Mensagens sem match são descartadas.
        # Matches reprovados pela IA também são guardados (com aprovado=False), mas
        # não disparam alerta.
        candidates: list[tuple[ProductInterest, float, float | None, dict[str, float], str | None, str | None, bool]] = []
        for interest in self.interests:
            if not interest.ativo:
                continue

            score, prices, breakdown, matched_keyword = composite_matcher.match(text, interest)

            threshold = interest.limiar_match or settings.match_score_threshold
            if score < threshold:
                continue

            preco = min(prices) if prices else None

            if interest.preco_maximo and preco and preco > interest.preco_maximo:
                logger.debug(
                    "price_above_max",
                    produto=interest.nome_produto,
                    preco=preco,
                    max=interest.preco_maximo,
                )
                continue

            ok, motivo = await self.llm_validator.validate(text, interest)
            if not ok:
                logger.info(
                    "llm_rejected",
                    produto=interest.nome_produto,
                    motivo=motivo,
                    chat=chat_name,
                )
                # Reprovado pela IA: registra o match (sem alertar) para auditoria.

            candidates.append((interest, score, preco, breakdown, matched_keyword, motivo, ok))

        if not candidates:
            return

        if self.message_repo.exists_by_telegram_id(message_id, chat_id):
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

        for interest, score, preco, breakdown, matched_keyword, motivo, aprovado in candidates:
            if self.match_repo.exists_by_message_and_interest(msg.id, interest.id):
                continue

            match = self.match_repo.create(
                message_id=msg.id,
                interest_id=interest.id,
                preco_encontrado=preco,
                score=score,
                raw_text_snippet=text[:300],
                matched_keyword=matched_keyword,
                llm_motivo=motivo,
                llm_aprovado=aprovado,
            )

            logger.info(
                "match_found",
                produto=interest.nome_produto,
                score=score,
                keyword_score=breakdown.get("keyword"),
                fuzzy_score=breakdown.get("fuzzy"),
                preco=preco,
                chat=chat_name,
                aprovado=aprovado,
            )

            # Reprovado pela IA fica registrado, mas não alerta via Telegram.
            if not aprovado:
                continue

            sent = await self.alert_service.send_alert(
                produto=interest.nome_produto,
                preco=f"R$ {preco:.2f}" if preco else "Não informado",
                link=build_message_link(chat_id, message_id),
                chat_id=chat_id,
                message_id=message_id,
                texto=text,
            )
            if sent:
                self.match_repo.mark_alerted(match.id)
