from telethon import TelegramClient

from app.core.config import settings


_client: TelegramClient | None = None
_bot_client: TelegramClient | None = None


def get_client() -> TelegramClient:
    global _client
    if _client is None:
        _client = TelegramClient(
            session=settings.telegram_session_file,
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
            device_model="PromoBot MVP",
            system_version="1.0",
            app_version="1.0.0",
        )
    return _client


def get_bot_client() -> TelegramClient:
    global _bot_client
    if _bot_client is None:
        _bot_client = TelegramClient(
            session=settings.telegram_bot_session_file,
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
            device_model="PromoBot MVP",
            system_version="1.0",
            app_version="1.0.0",
        )
    return _bot_client


async def is_connected() -> bool:
    client = get_client()
    return client.is_connected()
