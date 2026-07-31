import time

from fastapi import APIRouter

from app.telegram.auth import authenticator
from app.telegram.bot import bot_manager
from app.telegram.client import is_connected
from app.workers.supervisor import supervisor

public_router = APIRouter(tags=["Health"])
router = APIRouter(tags=["Health"])

_start_time = time.time()


@public_router.get("/healthz")
async def healthz():
    """Liveness para o HEALTHCHECK do container, que roda sem cookie."""
    return {"status": "ok"}


@router.get("/health")
async def health():
    connected = await is_connected()
    return {
        "status": "ok",
        "telegram_connected": connected,
        "telegram_authenticated": authenticator.is_authenticated,
        "worker_running": supervisor.is_running,
        "bot_connected": bot_manager.status().connected,
        "uptime_seconds": int(time.time() - _start_time),
    }
