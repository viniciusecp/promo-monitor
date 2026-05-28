import time

from fastapi import APIRouter

from app.telegram.client import is_connected

router = APIRouter(tags=["Health"])

_start_time = time.time()


@router.get("/health")
async def health():
    connected = await is_connected()
    return {
        "status": "ok",
        "telegram_connected": connected,
        "uptime_seconds": int(time.time() - _start_time),
    }
