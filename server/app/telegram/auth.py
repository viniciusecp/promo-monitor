"""Máquina de estados da autenticação do Telegram, dirigida por HTTP.

Antes o login acontecia com dois `input()` dentro do event loop do FastAPI — o
que travava a API inteira e obrigava um `docker attach` na primeira subida.
Aqui o mesmo fluxo vira estado explícito em memória: as rotas em
`app/api/routes/telegram_auth.py` empurram as transições e o frontend observa
`snapshot()` por polling.

Duas regras não negociáveis:

- **Nunca `client.start()` e nunca `input()`.** O `start()` do Telethon também
  faz prompt no stdin quando a sessão não está autorizada; só `connect()` é
  seguro aqui.
- **Nunca mandar código sozinho no boot.** Com `restart: on-failure:5` no
  compose, um reenvio automático queimaria um código por restart e levaria a um
  `FloodWaitError` de horas. Código só sai de um POST explícito.

O `phone_code_hash` não é guardado aqui de propósito: o Telethon o cacheia em
`client._phone_code_hash[phone]` e o `sign_in` o resolve sozinho. Guardar uma
segunda cópia só criaria uma chance de dessincronizar.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from telethon.errors import (
    ApiIdInvalidError,
    FloodWaitError,
    PasswordHashInvalidError,
    PhoneCodeEmptyError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    PhoneNumberUnoccupiedError,
    SessionPasswordNeededError,
)

from app.core.config import settings
from app.core.exceptions import (
    TelegramAuthBusyError,
    TelegramAuthError,
    TelegramAuthStateError,
)
from app.core.logging import logger
from app.core.masking import mask_phone
from app.core.timeutils import utcnow_naive
from app.telegram.client import get_client, reset_client

AuthStatus = Literal[
    "connecting",
    "unauthenticated",
    "awaiting_code",
    "awaiting_password",
    "authenticated",
    "error",
]


@dataclass
class AuthSnapshot:
    status: AuthStatus
    connected: bool
    phone_masked: str
    user_id: int | None = None
    username: str | None = None
    first_name: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    retry_after_seconds: int | None = None
    code_sent_at: datetime | None = None


# Exceção do Telethon -> (código estável da API, status resultante, mensagem pt-BR).
# `None` no status significa "mantém o estado atual".
_ERROR_MAP: dict[type[Exception], tuple[str, AuthStatus | None, str]] = {
    PhoneCodeInvalidError: (
        "code_invalid",
        "awaiting_code",
        "Código incorreto. Confira e tente de novo.",
    ),
    PhoneCodeEmptyError: (
        "code_invalid",
        "awaiting_code",
        "Código vazio. Digite o código que o Telegram enviou.",
    ),
    # Ao expirar, o Telethon descarta o phone_code_hash. Sem voltar para
    # `unauthenticated`, a próxima tentativa levantaria um ValueError opaco
    # ("You also need to provide a phone_code_hash") em vez de um erro tratável.
    PhoneCodeExpiredError: (
        "code_expired",
        "unauthenticated",
        "O código expirou. Peça um novo.",
    ),
    PasswordHashInvalidError: (
        "password_invalid",
        "awaiting_password",
        "Senha de duas etapas incorreta.",
    ),
    PhoneNumberInvalidError: (
        "phone_invalid",
        "error",
        "Número de telefone inválido. Corrija TELEGRAM_PHONE no server/.env.",
    ),
    PhoneNumberUnoccupiedError: (
        "phone_no_account",
        "error",
        "Não existe conta do Telegram para esse número.",
    ),
    ApiIdInvalidError: (
        "api_credentials_invalid",
        "error",
        "TELEGRAM_API_ID/TELEGRAM_API_HASH inválidos. Confira o server/.env.",
    ),
}


class TelegramAuthenticator:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._status: AuthStatus = "connecting"
        self._error: tuple[str, str, int | None] | None = None
        self._me = None
        self._code_sent_at: datetime | None = None

    # ------------------------------------------------------------------ leitura

    def snapshot(self) -> AuthSnapshot:
        """Estado atual sem nenhum round-trip. É polado a cada 3s pelo frontend
        e usado pelo `/health` — não pode fazer RPC nem pegar o lock."""
        client = get_client()
        code, message, retry_after = self._error or (None, None, None)
        return AuthSnapshot(
            status=self._status,
            connected=client.is_connected(),
            phone_masked=mask_phone(settings.telegram_phone),
            user_id=getattr(self._me, "id", None),
            username=getattr(self._me, "username", None),
            first_name=getattr(self._me, "first_name", None),
            error_code=code,
            error_message=message,
            retry_after_seconds=retry_after,
            code_sent_at=self._code_sent_at,
        )

    @property
    def is_authenticated(self) -> bool:
        return self._status == "authenticated"

    # ------------------------------------------------------------------ escrita

    async def bootstrap(self) -> AuthSnapshot:
        """Conecta e descobre se a sessão salva ainda vale. Não envia código."""
        async with self._lock:
            client = get_client()
            try:
                if not client.is_connected():
                    await client.connect()
                if await client.is_user_authorized():
                    await self._mark_authenticated(client)
                else:
                    self._status = "unauthenticated"
                    self._error = None
            except Exception as e:
                self._status = "error"
                self._error = ("not_connected", f"Falha ao conectar: {e}", None)
                logger.error("telegram_bootstrap_failed", error=str(e), exc_info=True)
                raise
            return self.snapshot()

    async def request_code(self) -> AuthSnapshot:
        if self._status == "authenticated":
            return self.snapshot()

        async with self._guard():
            client = await self._ensure_connected()
            phone = settings.telegram_phone
            try:
                await client.send_code_request(phone)
            except Exception as e:
                self._handle_error(e)
            self._status = "awaiting_code"
            self._error = None
            self._code_sent_at = utcnow_naive()
            logger.info("telegram_code_sent", phone=mask_phone(phone))
            return self.snapshot()

    async def submit_code(self, code: str) -> AuthSnapshot:
        self._require("awaiting_code")
        async with self._guard():
            client = await self._ensure_connected()
            try:
                await client.sign_in(phone=settings.telegram_phone, code=code.strip())
            except SessionPasswordNeededError:
                self._status = "awaiting_password"
                self._error = None
                logger.info("telegram_2fa_required")
                return self.snapshot()
            except Exception as e:
                self._handle_error(e)
            await self._mark_authenticated(client)
            return self.snapshot()

    async def submit_password(self, password: str) -> AuthSnapshot:
        self._require("awaiting_password")
        async with self._guard():
            client = await self._ensure_connected()
            try:
                await client.sign_in(password=password)
            except Exception as e:
                self._handle_error(e)
            await self._mark_authenticated(client)
            return self.snapshot()

    async def logout(self) -> AuthSnapshot:
        async with self._guard():
            client = get_client()
            try:
                if client.is_connected():
                    await client.log_out()
            except Exception as e:
                logger.warning("telegram_logout_failed", error=str(e))
            # Depois do log_out a sessão do objeto está morta; descartar o
            # singleton para que o próximo login construa um cliente novo.
            await reset_client(delete_session=True)
            self._status = "unauthenticated"
            self._error = None
            self._me = None
            self._code_sent_at = None
            logger.info("telegram_logged_out")
            return self.snapshot()

    def mark_session_revoked(self) -> None:
        """Chamado pelo watchdog quando a sessão é derrubada de outro aparelho."""
        self._status = "unauthenticated"
        self._me = None
        self._error = (
            "session_revoked",
            "A sessão foi encerrada pelo Telegram. Entre de novo.",
            None,
        )

    # ------------------------------------------------------------------ internos

    def _guard(self):
        """Lock com falha rápida — nunca enfileira uma segunda operação."""
        if self._lock.locked():
            raise TelegramAuthBusyError()
        return self._lock

    def _require(self, expected: AuthStatus) -> None:
        if self._status != expected:
            raise TelegramAuthStateError(expected=expected, actual=self._status)

    async def _ensure_connected(self):
        client = get_client()
        if not client.is_connected():
            try:
                await client.connect()
            except Exception as e:
                self._status = "error"
                self._error = ("not_connected", f"Sem conexão com o Telegram: {e}", None)
                raise TelegramAuthError("not_connected", str(e)) from e
        return client

    async def _mark_authenticated(self, client) -> None:
        self._me = await client.get_me()
        self._status = "authenticated"
        self._error = None
        self._code_sent_at = None
        logger.info(
            "telegram_authenticated",
            username=getattr(self._me, "username", None),
            phone=mask_phone(settings.telegram_phone),
        )

    def _handle_error(self, exc: Exception) -> None:
        """Traduz a exceção do Telethon, atualiza o estado e levanta
        `TelegramAuthError`. Nunca retorna."""
        if isinstance(exc, FloodWaitError):
            seconds = int(getattr(exc, "seconds", 0) or 0)
            self._error = (
                "flood_wait",
                f"Muitas tentativas. Aguarde {seconds}s antes de tentar de novo.",
                seconds,
            )
            logger.warning("telegram_flood_wait", seconds=seconds)
            raise TelegramAuthError("flood_wait", self._error[1], retry_after=seconds)

        for exc_type, (code, status, message) in _ERROR_MAP.items():
            if isinstance(exc, exc_type):
                if status is not None:
                    self._status = status
                self._error = (code, message, None)
                logger.warning("telegram_auth_error", code=code)
                raise TelegramAuthError(code, message) from exc

        if isinstance(exc, (ConnectionError, OSError)):
            self._status = "error"
            self._error = ("not_connected", "Sem conexão com o Telegram.", None)
            logger.error("telegram_connection_error", error=str(exc))
            raise TelegramAuthError("not_connected", self._error[1]) from exc

        self._status = "error"
        self._error = ("unknown", f"Erro inesperado: {exc}", None)
        logger.error("telegram_auth_unknown_error", error=str(exc), exc_info=True)
        raise TelegramAuthError("unknown", self._error[1]) from exc


authenticator = TelegramAuthenticator()
