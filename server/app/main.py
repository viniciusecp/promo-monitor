import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.deps import RENEW_FLAG, set_session_cookie
from app.api.router import api_router
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.database.base import Base
from app.database.session import SessionLocal, engine, ensure_columns, ensure_indexes
from app.repositories.user_repo import SessionRepository, UserRepository
from app.services.auth_service import AuthService
from app.telegram.client import disconnect_clients
from app.workers.supervisor import supervisor
from app.workers.telegram_worker import run_telegram_worker

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def _bootstrap_auth() -> None:
    """Sessão própria e curta: a do supervisor é de vida longa, e reusá-la
    deixaria esta transação aberta pelo resto do processo.
    """
    db = SessionLocal()
    try:
        service = AuthService(UserRepository(db), SessionRepository(db))
        service.seed_owner()
        removidas = service.purge_expired()
        if removidas:
            logger.info("sessions_purged", total=removidas)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    Base.metadata.create_all(bind=engine)
    ensure_columns()
    ensure_indexes()
    _bootstrap_auth()
    logger.info("database_ready")

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


@app.middleware("http")
async def renew_session_cookie(request: Request, call_next):
    """A metade que falta do login persistente.

    `resolve_session` estende a validade no banco, mas quem manda no navegador é
    o `max_age` do cookie — sem reemitir, ele morreria 30 dias após o login
    mesmo com o painel em uso diário. A dependência só marca a request; o
    `Set-Cookie` sai daqui, onde a resposta real já existe.
    """
    response = await call_next(request)
    token = getattr(request.state, RENEW_FLAG, None)
    if token:
        set_session_cookie(response, token)
    return response


@app.middleware("http")
async def block_cross_origin_writes(request: Request, call_next):
    """Segunda camada de CSRF, depois do `SameSite=Lax` do cookie.

    Origin ausente é aceito: `curl` e o healthcheck não mandam o header, e aí
    não há navegador para ser enganado.
    """
    if request.method not in _SAFE_METHODS:
        origin = request.headers.get("origin")
        if origin:
            permitidas = {*settings.cors_origins}
            esperada = f"{request.url.scheme}://{request.headers.get('host', '')}"
            if origin not in permitidas and origin != esperada:
                logger.warning("cross_origin_write_blocked", origin=origin)
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": {
                            "code": "cross_origin",
                            "message": "Origem não permitida.",
                        }
                    },
                )
    return await call_next(request)


if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=True,
    )
