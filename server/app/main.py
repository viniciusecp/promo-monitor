import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.database.base import Base
from app.database.session import engine, ensure_columns
from app.telegram.client import disconnect_clients
from app.workers.supervisor import supervisor
from app.workers.telegram_worker import run_telegram_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    Base.metadata.create_all(bind=engine)
    ensure_columns()
    logger.info("database_ready")

    # O boot é assíncrono de propósito: se não houver sessão válida ele apenas
    # loga e sai, e a API sobe para servir a tela de login.
    app.state.telegram_task = asyncio.create_task(
        run_telegram_worker(), name="telegram_boot"
    )
    logger.info("telegram_boot_scheduled")

    yield

    app.state.telegram_task.cancel()
    try:
        await app.state.telegram_task
    except asyncio.CancelledError:
        pass
    await supervisor.stop()
    await disconnect_clients()
    logger.info("shutdown_complete")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
