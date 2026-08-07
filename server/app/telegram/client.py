from pathlib import Path

from telethon import TelegramClient

from app.core.config import settings
from app.core.logging import logger


_client: TelegramClient | None = None
_bot_client: TelegramClient | None = None

_receive_updates: bool = True


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
            receive_updates=_receive_updates,
        )
    return _client


def receives_updates() -> bool:
    return _receive_updates


async def set_receive_updates(enabled: bool) -> bool:
    global _receive_updates
    if _receive_updates == enabled:
        return False

    _receive_updates = enabled
    await reset_client(delete_session=False)
    client = get_client()
    await client.connect()
    logger.info("telegram_receive_updates_changed", enabled=enabled)
    return True


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


async def is_authorized() -> bool:
    client = get_client()
    if not client.is_connected():
        return False
    try:
        return await client.is_user_authorized()
    except Exception as e:
        logger.warning("is_authorized_failed", error=str(e))
        return False


def _delete_session_files(path_str: str) -> None:
    path = Path(path_str)
    for candidate in (path, path.with_name(path.name + "-journal")):
        try:
            candidate.unlink(missing_ok=True)
        except OSError as e:
            logger.warning("session_unlink_failed", path=str(candidate), error=str(e))


async def _disconnect(client: TelegramClient | None) -> None:
    if client is None or not client.is_connected():
        return
    try:
        result = client.disconnect()
        if result is not None:
            await result
    except Exception as e:
        logger.warning("client_disconnect_failed", error=str(e))


async def reset_client(delete_session: bool = False) -> None:
    """Descarta o cliente de usuário para que o próximo `get_client()` construa um novo."""
    global _client
    await _disconnect(_client)
    _client = None
    if delete_session:
        _delete_session_files(settings.telegram_session_file)


async def reset_bot_client(delete_session: bool = False) -> None:
    """Idem para o bot."""
    global _bot_client
    await _disconnect(_bot_client)
    _bot_client = None
    if delete_session:
        _delete_session_files(settings.telegram_bot_session_file)


async def disconnect_clients() -> None:
    """Desconecta os dois clientes no shutdown, sem descartar os singletons."""
    await _disconnect(_client)
    await _disconnect(_bot_client)
