"""Rotina de boot do Telegram."""

import asyncio

from app.core.logging import logger
from app.telegram.auth import authenticator
from app.workers.supervisor import supervisor

_CONNECT_ATTEMPTS = 5
_CONNECT_BACKOFF = 3


async def run_telegram_worker() -> None:
    snapshot = None

    for attempt in range(1, _CONNECT_ATTEMPTS + 1):
        try:
            snapshot = await authenticator.bootstrap()
            break
        except Exception as e:
            if attempt == _CONNECT_ATTEMPTS:
                logger.error(
                    "telegram_boot_failed",
                    error=str(e),
                    attempts=attempt,
                    exc_info=True,
                )
                return
            logger.warning(
                "telegram_boot_retry", error=str(e), attempt=attempt
            )
            await asyncio.sleep(_CONNECT_BACKOFF * attempt)

    if snapshot is None or snapshot.status != "authenticated":
        logger.warning(
            "telegram_login_required",
            hint="abra o painel e faça o login em /login",
        )
        return

    try:
        await supervisor.ensure_started()
    except Exception as e:
        logger.error("worker_bootstrap_failed", error=str(e), exc_info=True)
