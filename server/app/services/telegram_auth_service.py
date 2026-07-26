"""Orquestra a máquina de autenticação com o ciclo de vida do pipeline.

O `TelegramAuthenticator` só sabe autenticar; é aqui que "autenticou" vira
"começa a capturar mensagens" e "saiu" vira "para tudo".
"""

from app.core.logging import logger
from app.telegram.auth import AuthSnapshot, authenticator
from app.telegram.bot import bot_manager
from app.workers.supervisor import supervisor


class TelegramAuthService:
    async def status(self) -> dict:
        return self._to_dict(authenticator.snapshot())

    async def request_code(self) -> dict:
        return self._to_dict(await authenticator.request_code())

    async def submit_code(self, code: str) -> dict:
        return await self._after_login(await authenticator.submit_code(code))

    async def submit_password(self, password: str) -> dict:
        return await self._after_login(await authenticator.submit_password(password))

    async def logout(self) -> dict:
        await supervisor.stop()
        await bot_manager.stop()
        return self._to_dict(await authenticator.logout())

    async def _after_login(self, snapshot: AuthSnapshot) -> dict:
        if snapshot.status == "authenticated":
            # Uma falha ao subir o pipeline não pode derrubar a resposta do
            # login: o usuário está autenticado de qualquer forma, e o painel
            # mostra `worker_running: false` com o erro em Configurações.
            try:
                await supervisor.ensure_started()
            except Exception as e:
                logger.error("worker_start_after_login_failed", error=str(e), exc_info=True)
        return self._to_dict(snapshot)

    def _to_dict(self, snapshot: AuthSnapshot) -> dict:
        user = None
        if snapshot.user_id is not None:
            user = {
                "id": snapshot.user_id,
                "first_name": snapshot.first_name,
                "username": snapshot.username,
            }
        return {
            "status": snapshot.status,
            "connected": snapshot.connected,
            "phone_masked": snapshot.phone_masked,
            "worker_running": supervisor.is_running,
            "user": user,
            "error_code": snapshot.error_code,
            "error_message": snapshot.error_message,
            "retry_after_seconds": snapshot.retry_after_seconds,
            "code_sent_at": snapshot.code_sent_at,
            "can_request_code": snapshot.status != "authenticated",
        }


telegram_auth_service = TelegramAuthService()
