from telethon import TelegramClient
from telethon.events import NewMessage

from app.core.config import settings
from app.core.logging import logger
from app.repositories.app_config_repo import AppConfigRepository


async def start_bot(bot_client: TelegramClient, session_factory) -> bool:
    """Inicia o bot de notificações e registra os comandos.

    Sem `TELEGRAM_BOT_TOKEN` configurado, não inicia (e nenhuma notificação é
    enviada). O comando `/start` salva o chat de quem mandou em
    `app_config.alert_target`, deixando o setup das notificações em um clique.
    """
    if not settings.telegram_bot_token:
        logger.warning("bot_disabled_no_token")
        return False

    await bot_client.start(bot_token=settings.telegram_bot_token)

    async def _on_start(event: NewMessage.Event) -> None:
        chat_id = event.chat_id
        db = session_factory()
        try:
            AppConfigRepository(db).set_target(str(chat_id))
        finally:
            db.close()
        await event.respond(
            "✅ Notificações ativadas neste chat. Você receberá aqui as promoções "
            "encontradas."
        )
        logger.info("bot_target_set", chat_id=chat_id)

    async def _on_id(event: NewMessage.Event) -> None:
        await event.respond(f"Seu chat_id é `{event.chat_id}`")

    bot_client.add_event_handler(_on_start, NewMessage(pattern=r"^/start"))
    bot_client.add_event_handler(_on_id, NewMessage(pattern=r"^/id"))

    me = await bot_client.get_me()
    logger.info("bot_started", username=getattr(me, "username", None))
    return True
