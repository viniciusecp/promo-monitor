from fastapi import APIRouter

from app.core.logging import logger
from app.telegram.client import get_client

router = APIRouter(prefix="/telegram", tags=["Telegram"])


def _chat_type(dialog) -> str:
    if dialog.is_channel:
        return "channel"
    if dialog.is_group:
        return "group"
    if dialog.is_user:
        return "user"
    return "other"


@router.get("/chats")
async def list_chats() -> list[dict]:
    client = get_client()
    if not client.is_connected():
        return []

    try:
        dialogs = await client.get_dialogs()
    except Exception as e:
        logger.warning("list_chats_failed", error=str(e))
        return []

    chats = [
        {"id": str(d.id), "title": d.name, "type": _chat_type(d)}
        for d in dialogs
        if d.name
    ]
    chats.sort(key=lambda c: c["title"].lower())
    return chats
