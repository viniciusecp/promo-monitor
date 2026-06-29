from telethon import TelegramClient

from app.core.logging import logger
from app.repositories.app_config_repo import AppConfigRepository


def _resolve_target(raw: str | None):
    """Resolve o destino do alerta para algo que o Telethon aceite.

    Vazio/branco -> None (não envia nada). Numérico (ex.: -100123) -> int.
    Caso contrário, a própria string (@username / username).
    """
    if not raw or not raw.strip():
        return None
    raw = raw.strip()
    if raw.lstrip("-").isdigit():
        return int(raw)
    return raw


def _build_body(produto: str, preco: str, texto: str | None, link: str) -> str:
    parts = [f"🚨 Promo: {produto} — {preco}"]
    if texto:
        trecho = texto.strip()
        if len(trecho) > 500:
            trecho = trecho[:500] + "…"
        parts.append("")
        parts.append(trecho)
    parts.append("")
    parts.append(f"🔗 {link}")
    return "\n".join(parts)


class AlertService:
    def __init__(self, bot_client: TelegramClient, session_factory) -> None:
        self.bot_client = bot_client
        self.session_factory = session_factory

    def _get_target(self):
        db = self.session_factory()
        try:
            raw = AppConfigRepository(db).get_or_create().alert_target
        finally:
            db.close()
        return raw

    async def send_alert(
        self,
        produto: str,
        preco: str,
        link: str,
        chat_id: int,
        message_id: int,
        texto: str | None = None,
    ) -> bool:
        try:
            target = _resolve_target(self._get_target())
            if target is None:
                logger.info("alert_skipped_no_target", produto=produto)
                return False

            if self.bot_client is None or not self.bot_client.is_connected():
                logger.warning("alert_skipped_bot_unavailable", produto=produto)
                return False

            body = _build_body(produto, preco, texto, link)
            await self.bot_client.send_message(target, body)
            logger.info("alert_sent", produto=produto, target=str(target))
            return True
        except Exception as e:
            logger.error("alert_failed", error=str(e), produto=produto)
            return False
