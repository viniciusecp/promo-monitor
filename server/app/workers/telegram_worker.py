"""Rotina de boot do Telegram.

Conecta e, se a sessão salva ainda valer, sobe o pipeline como antes. Se não
valer, **não faz nada** e apenas registra que falta login: o usuário resolve
pelo painel (`/login` → `POST /telegram/auth/request-code`). Nada de `input()`,
nada de bloquear o event loop, e nada de mandar código sozinho — com
`restart: on-failure:5` no compose isso queimaria um código por restart até cair
num FloodWait de horas.
"""

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
            # Em Docker a rede pode não estar pronta na primeira tentativa.
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
