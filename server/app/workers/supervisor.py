"""Supervisor do pipeline de captura — idempotente e religável em runtime."""

from __future__ import annotations

import asyncio
from datetime import datetime

from app.core.logging import logger
from app.core.timeutils import utcnow_naive
from app.database.session import SessionLocal
from app.repositories.interest_repo import InterestRepository
from app.repositories.match_repo import MatchRepository
from app.repositories.message_repo import MessageRepository
from app.services.alert_service import AlertService
from app.services.llm_validator_service import LLMValidator
from app.services.message_service import MessageService
from app.telegram.auth import authenticator
from app.telegram.bot import bot_manager
from app.telegram.client import get_client
from app.telegram.listener import MessageListener

_REFRESH_INTERVAL = 60
_WATCHDOG_INTERVAL = 30
_AUTH_CHECK_EVERY = 10


class WorkerSupervisor:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._started = False
        self._db = None
        self._listener: MessageListener | None = None
        self._message_service: MessageService | None = None
        self._refresh_task: asyncio.Task | None = None
        self._watchdog_task: asyncio.Task | None = None
        self._started_at: datetime | None = None
        self._interests_count = 0
        self._last_error: str | None = None

    @property
    def is_running(self) -> bool:
        return self._started

    def status(self) -> dict:
        return {
            "running": self._started,
            "started_at": self._started_at,
            "interests_count": self._interests_count,
            "last_error": self._last_error,
        }

    async def ensure_started(self) -> bool:
        async with self._lock:
            if self._started:
                return True

            client = get_client()
            if not client.is_connected() or not await client.is_user_authorized():
                logger.warning("worker_start_skipped_not_authorized")
                return False

            try:
                await self._build(client)
            except Exception as e:
                self._last_error = str(e)
                logger.error("worker_start_failed", error=str(e), exc_info=True)
                await self._teardown()
                return False

            self._started = True
            self._started_at = utcnow_naive()
            self._last_error = None
            logger.info("worker_started", interests_count=self._interests_count)
            return True

    async def stop(self) -> None:
        async with self._lock:
            if not self._started and self._db is None:
                return
            await self._teardown()
            self._started = False
            self._started_at = None
            logger.info("worker_stopped")

    # ------------------------------------------------------------------ internos

    async def _build(self, client) -> None:
        self._db = SessionLocal()

        interest_repo = InterestRepository(self._db)
        message_repo = MessageRepository(self._db)
        match_repo = MatchRepository(self._db)
        interests = interest_repo.list_active()
        self._interests_count = len(interests)

        try:
            await bot_manager.ensure_started(SessionLocal)
        except Exception as e:
            logger.error("bot_start_failed_nonfatal", error=str(e), exc_info=True)

        alert_service = AlertService(
            bot_provider=bot_manager.get_client,
            session_factory=SessionLocal,
        )
        self._message_service = MessageService(
            message_repo=message_repo,
            match_repo=match_repo,
            alert_service=alert_service,
            llm_validator=LLMValidator(),
            interests=interests,
        )

        self._listener = MessageListener(
            client=client,
            message_service=self._message_service,
        )
        await self._listener.start()

        self._listener = MessageListener(
            self._refresh_loop(), name="refresh_interests"
        )
        self._watchdog_task = asyncio.create_task(
            self._watchdog_loop(), name="telegram_watchdog"
        )

    async def _teardown(self) -> None:
        for task in (self._refresh_task, self._watchdog_task):
            if task is not None and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.warning("worker_task_teardown_error", error=str(e))
        self._refresh_task = None
        self._watchdog_task = None

        if self._listener is not None:
            await self._listener.stop()
            self._listener = None

        self._message_service = None

        if self._db is not None:
            self._db.close()
            self._db = None

    async def _refresh_loop(self) -> None:
        while True:
            await asyncio.sleep(_REFRESH_INTERVAL)
            try:
                db = SessionLocal()
                try:
                    active = InterestRepository(db).list_active()
                finally:
                    db.close()
                if self._message_service is not None:
                    self._message_service.refresh_interests(active)
                    self._interests_count = len(active)
                logger.debug("interests_refreshed", count=len(active))
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error("interests_refresh_failed", error=str(e), exc_info=True)

    async def _watchdog_loop(self) -> None:
        tick = 0
        while True:
            await asyncio.sleep(_WATCHDOG_INTERVAL)
            tick += 1
            try:
                client = get_client()

                if not client.is_connected():
                    logger.warning("telegram_disconnected_reconnecting")
                    await client.connect()

                if tick % _AUTH_CHECK_EVERY == 0:
                    if not await client.is_user_authorized():
                        logger.warning("telegram_session_revoked")
                        authenticator.mark_session_revoked()
                        asyncio.create_task(self.stop(), name="worker_stop_revoked")
                        return
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error("watchdog_tick_failed", error=str(e), exc_info=True)


supervisor = WorkerSupervisor()
