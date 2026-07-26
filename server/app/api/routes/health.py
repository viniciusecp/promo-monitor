import time

from fastapi import APIRouter

from app.telegram.auth import authenticator
from app.telegram.bot import bot_manager
from app.telegram.client import is_connected
from app.workers.supervisor import supervisor

router = APIRouter(tags=["Health"])

_start_time = time.time()


@router.get("/health")
async def health():
    connected = await is_connected()
    # Tudo aqui sai de snapshot em memória — este endpoint é polado a cada 15s
    # pelo frontend e não pode custar um round-trip ao Telegram.
    return {
        "status": "ok",
        "telegram_connected": connected,
        "telegram_authenticated": authenticator.is_authenticated,
        "worker_running": supervisor.is_running,
        "bot_connected": bot_manager.status().connected,
        "uptime_seconds": int(time.time() - _start_time),
    }
