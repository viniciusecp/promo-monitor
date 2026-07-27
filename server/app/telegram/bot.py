"""Bot de notificações — ciclo de vida trocável a quente.

O token vive em `app_config.telegram_bot_token` (o `.env` só semeia o valor
inicial), então salvar um token novo no painel precisa valer sem reiniciar o
container. Isso obriga a um cuidado específico: o `start(bot_token=...)` do
Telethon só faz sign-in quando a sessão ainda **não** está autorizada. Com um
`bot.session` do bot anterior no disco, a troca de token pareceria funcionar e
os alertas continuariam saindo pelo bot antigo. Por isso o `stop()` apaga o
arquivo de sessão e a subida usa `connect()` + `sign_in(bot_token=...)`.

Um token inválido nunca sobe para o chamador: fica em `last_error` e aparece no
painel. O listener de mensagens não pode deixar de subir por causa do bot.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from telethon import TelegramClient
from telethon.events import NewMessage

from app.core.logging import logger
from app.core.masking import mask_token
from app.repositories.app_config_repo import AppConfigRepository
from app.telegram.auth import authenticator
from app.telegram.client import get_bot_client, reset_bot_client


@dataclass
class BotSnapshot:
    configured: bool
    connected: bool
    username: str | None = None
    last_error: str | None = None


def _read_token(session_factory) -> str | None:
    db = session_factory()
    try:
        return AppConfigRepository(db).get_or_create().telegram_bot_token or None
    finally:
        db.close()


class BotManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._client: TelegramClient | None = None
        self._running_token: str | None = None
        self._username: str | None = None
        self._last_error: str | None = None

    def get_client(self) -> TelegramClient | None:
        """Resolvido a cada envio pelo `AlertService` — nunca guardar o
        resultado, senão uma troca de token deixa uma referência morta."""
        return self._client

    def status(self) -> BotSnapshot:
        return BotSnapshot(
            configured=self._running_token is not None,
            connected=self._client is not None and self._client.is_connected(),
            username=self._username,
            last_error=self._last_error,
        )

    def snapshot_for(self, token: str | None) -> BotSnapshot:
        """Status combinado com o token gravado no banco — `configured` reflete
        o que está salvo, não só o que conseguiu subir."""
        snap = self.status()
        snap.configured = bool(token)
        return snap

    async def ensure_started(self, session_factory) -> BotSnapshot:
        token = _read_token(session_factory)
        async with self._lock:
            if token and token == self._running_token and self._is_live():
                return self.snapshot_for(token)
            await self._restart(token, session_factory)
        return self.snapshot_for(token)

    async def apply_token(self, token: str | None, session_factory) -> BotSnapshot:
        async with self._lock:
            if token == self._running_token and self._is_live():
                return self.snapshot_for(token)
            await self._restart(token, session_factory)
        return self.snapshot_for(token)

    async def stop(self) -> None:
        async with self._lock:
            await self._teardown()

    # ------------------------------------------------------------------ internos

    def _is_live(self) -> bool:
        return self._client is not None and self._client.is_connected()

    async def _teardown(self) -> None:
        # Desconecta e apaga `bot.session`. Não faz `log_out()` de propósito:
        # é um round-trip que pode travar e não agrega nada — apagar o arquivo
        # local já é o que torna a troca de token efetiva, e uma autorização
        # órfã de bot no lado do Telegram é inofensiva.
        await reset_bot_client(delete_session=True)
        self._client = None
        self._running_token = None
        self._username = None

    async def _restart(self, token: str | None, session_factory) -> None:
        await self._teardown()

        if not token:
            self._last_error = None
            logger.warning("bot_disabled_no_token")
            return

        client = get_bot_client()
        try:
            await client.connect()
            await client.sign_in(bot_token=token)
            self._register_handlers(client, session_factory)
            me = await client.get_me()
            self._client = client
            self._running_token = token
            self._username = getattr(me, "username", None)
            self._last_error = None
            logger.info(
                "bot_started",
                username=self._username,
                token=mask_token(token),
            )
        except Exception as e:
            self._last_error = str(e)
            self._client = None
            self._running_token = None
            self._username = None
            await reset_bot_client(delete_session=True)
            logger.error("bot_start_failed", error=str(e), token=mask_token(token))

    def _register_handlers(self, client: TelegramClient, session_factory) -> None:
        async def _on_start(event: NewMessage.Event) -> None:
            # O username de um bot é público e pesquisável, e `alert_target` é
            # um campo só. Sem esta checagem, um `/start` de qualquer estranho
            # *sequestraria* o destino: ele passaria a receber as promoções e o
            # dono pararia de receber, em silêncio. Quem autoriza é o remetente,
            # não o chat — mandar `/start` de dentro de um grupo continua
            # apontando o alerta para o grupo.
            owner_id = authenticator.user_id
            sender_id = event.sender_id

            if owner_id is None:
                # Fecha em vez de abrir. Esta janela existe de verdade: o token
                # é salvo pelo painel, que não exige login, então o bot pode
                # estar no ar antes de a conta de usuário ter sido conectada —
                # e é justamente aí que não há com quem comparar.
                await event.respond(
                    "⚠️ Conecte a sua conta do Telegram no painel antes de ativar "
                    "as notificações."
                )
                logger.warning("bot_target_denied_no_owner", sender_id=sender_id)
                return

            if sender_id != owner_id:
                # Resposta neutra de propósito: não confirma para o estranho que
                # ele achou o bot certo nem revela nada do dono.
                await event.respond("Este bot é privado.")
                logger.warning(
                    "bot_target_denied",
                    sender_id=sender_id,
                    chat_id=event.chat_id,
                )
                return

            chat_id = event.chat_id
            db = session_factory()
            try:
                AppConfigRepository(db).set_target(str(chat_id))
            finally:
                db.close()
            await event.respond(
                "✅ Notificações ativadas neste chat. Você receberá aqui as promoções "
                "encontradas."
            )
            logger.info("bot_target_set", chat_id=chat_id)

        async def _on_id(event: NewMessage.Event) -> None:
            await event.respond(f"Seu chat_id é `{event.chat_id}`")

        client.add_event_handler(_on_start, NewMessage(pattern=r"^/start"))
        client.add_event_handler(_on_id, NewMessage(pattern=r"^/id"))


bot_manager = BotManager()
