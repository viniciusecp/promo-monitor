from datetime import datetime, timezone

from telethon import TelegramClient
from telethon.events import NewMessage

from app.core.logging import logger
from app.services.message_service import MessageService


class MessageListener:
    def __init__(self, client: TelegramClient, message_service: MessageService) -> None:
        self.client = client
        self.message_service = message_service
        self._handler_registered = False

    async def start(self) -> None:
        if self._handler_registered:
            return

        self.client.add_event_handler(
            self._on_new_message,
            NewMessage(incoming=True, func=lambda e: e.is_group or e.is_channel),
        )
        self._handler_registered = True
        logger.info("listener_started")

    async def stop(self) -> None:
        if not self._handler_registered:
            return
        try:
            self.client.remove_event_handler(self._on_new_message)
        except Exception as e:
            logger.warning("listener_stop_failed", error=str(e))
        self._handler_registered = False
        logger.info("listener_stopped")

    async def _on_new_message(self, event: NewMessage.Event) -> None:
        try:
            if event.is_private:
                return

            msg = event.message
            chat = await event.get_chat()
            sender = await event.get_sender()

            chat_name = getattr(chat, "title", None) or getattr(chat, "username", None)
            sender_name = getattr(sender, "first_name", None) or getattr(sender, "username", None)
            sender_id = getattr(sender, "id", None)

            await self.message_service.process_message(
                message_id=msg.id,
                chat_id=msg.chat_id,
                chat_name=chat_name,
                sender_id=sender_id,
                sender_name=sender_name,
                text=msg.text or msg.message,
                raw_date=msg.date.replace(tzinfo=timezone.utc) if msg.date else None,
            )
        except Exception as e:
            logger.error("listener_error", error=str(e), exc_info=True)
