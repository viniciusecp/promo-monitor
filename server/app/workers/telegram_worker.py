import asyncio

from app.core.config import settings
from app.core.logging import logger
from app.database.session import SessionLocal
from app.repositories.interest_repo import InterestRepository
from app.repositories.match_repo import MatchRepository
from app.repositories.message_repo import MessageRepository
from app.services.alert_service import AlertService
from app.services.llm_validator_service import LLMValidator
from app.services.message_service import MessageService
from app.telegram.auth import ensure_authenticated
from app.telegram.bot import start_bot
from app.telegram.client import get_bot_client, get_client
from app.telegram.listener import MessageListener


async def run_telegram_worker() -> None:
    client = get_client()
    await client.start()
    phone = settings.telegram_phone
    await ensure_authenticated(client, phone)

    bot_client = get_bot_client()
    await start_bot(bot_client, SessionLocal)

    db = SessionLocal()
    try:
        interest_repo = InterestRepository(db)
        message_repo = MessageRepository(db)
        match_repo = MatchRepository(db)
        interests = interest_repo.list_active()

        alert_service = AlertService(bot_client, SessionLocal)
        llm_validator = LLMValidator()

        message_service = MessageService(
            message_repo=message_repo,
            match_repo=match_repo,
            alert_service=alert_service,
            llm_validator=llm_validator,
            interests=interests,
        )

        listener = MessageListener(client=client, message_service=message_service)
        await listener.start()

        logger.info(
            "worker_started",
            chats_count=len(await client.get_dialogs()),
            interests_count=len(interests),
        )

        async def refresh_interests() -> None:
            while True:
                await asyncio.sleep(60)
                db2 = SessionLocal()
                try:
                    repo2 = InterestRepository(db2)
                    active = repo2.list_active()
                    message_service.refresh_interests(active)
                    logger.debug("interests_refreshed", count=len(active))
                finally:
                    db2.close()

        asyncio.create_task(refresh_interests())

        await client.run_until_disconnected()
    finally:
        db.close()
