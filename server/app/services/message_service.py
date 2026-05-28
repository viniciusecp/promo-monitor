import re
from datetime import datetime

from app.core.config import settings
from app.core.logging import logger
from app.models.product_interest import ProductInterest
from app.models.telegram_message import TelegramMessage
from app.repositories.match_repo import MatchRepository
from app.repositories.message_repo import MessageRepository
from app.services.alert_service import AlertService
from app.services.matcher_service import composite_matcher, normalize_text


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
        interests: list[ProductInterest],
    ) -> None:
        self.message_repo = message_repo
        self.match_repo = match_repo
        self.alert_service = alert_service
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

        normalized = normalize_text(text)

        for interest in self.interests:
            if not interest.ativo:
                continue

            excl_hit = False
            for excl in interest.palavras_excluidas:
                if normalize_text(excl) in normalized:
                    excl_hit = True
                    break
            if excl_hit:
                continue

            score, prices = composite_matcher.match(text, interest)

            if score < settings.match_score_threshold:
                continue

            if self.match_repo.exists_by_message_and_interest(msg.id, interest.id):
                continue

            preco = prices[0] if prices else None

            if interest.preco_maximo and preco and preco > interest.preco_maximo:
                logger.debug(
                    "price_above_max",
                    produto=interest.nome_produto,
                    preco=preco,
                    max=interest.preco_maximo,
                )
                continue

            self.match_repo.create(
                message_id=msg.id,
                interest_id=interest.id,
                preco_encontrado=preco,
                score=score,
                raw_text_snippet=text[:300],
            )

            logger.info(
                "match_found",
                produto=interest.nome_produto,
                score=score,
                preco=preco,
                chat=chat_name,
            )

            await self.alert_service.send_alert(
                produto=interest.nome_produto,
                preco=f"R$ {preco:.2f}" if preco else "Não informado",
                grupo=chat_name or "Desconhecido",
                score=score,
                texto=text,
                link=build_message_link(chat_id, message_id),
            )
