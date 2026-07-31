"""Login do Telegram pela web."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_owner
from app.core.exceptions import (
    TelegramAuthBusyError,
    TelegramAuthError,
    TelegramAuthStateError,
)
from app.schemas.telegram_auth import (
    AuthCodeRequest,
    AuthPasswordRequest,
    AuthStatusResponse,
)
from app.services.telegram_auth_service import telegram_auth_service

router = APIRouter(
    prefix="/telegram/auth",
    tags=["Telegram Auth"],
    dependencies=[Depends(require_owner)],
)

_STATUS_BY_CODE = {
    "code_invalid": 400,
    "code_expired": 400,
    "password_invalid": 400,
    "phone_invalid": 400,
    "phone_no_account": 400,
    "api_credentials_invalid": 400,
    "flood_wait": 429,
    "not_connected": 503,
}


def _raise(exc: TelegramAuthError) -> None:
    status = _STATUS_BY_CODE.get(exc.code, 500)
    headers = None
    if exc.retry_after is not None:
        headers = {"Retry-After": str(exc.retry_after)}
    raise HTTPException(
        status_code=status,
        detail={
            "code": exc.code,
            "message": exc.message,
            "retry_after": exc.retry_after,
        },
        headers=headers,
    )


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status():
    return await telegram_auth_service.status()


@router.post("/request-code", response_model=AuthStatusResponse)
async def request_code():
    try:
        return await telegram_auth_service.request_code()
    except TelegramAuthBusyError:
        raise HTTPException(
            status_code=409,
            detail={"code": "auth_busy", "message": "Outra operação de login está em andamento."},
        )
    except TelegramAuthError as e:
        _raise(e)


@router.post("/code", response_model=AuthStatusResponse)
async def submit_code(data: AuthCodeRequest):
    try:
        return await telegram_auth_service.submit_code(data.code)
    except TelegramAuthBusyError:
        raise HTTPException(
            status_code=409,
            detail={"code": "auth_busy", "message": "Outra operação de login está em andamento."},
        )
    except TelegramAuthStateError as e:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "wrong_state",
                "message": f"O login não está esperando um código (estado atual: {e.actual}).",
            },
        )
    except TelegramAuthError as e:
        _raise(e)


@router.post("/password", response_model=AuthStatusResponse)
async def submit_password(data: AuthPasswordRequest):
    try:
        return await telegram_auth_service.submit_password(data.password)
    except TelegramAuthBusyError:
        raise HTTPException(
            status_code=409,
            detail={"code": "auth_busy", "message": "Outra operação de login está em andamento."},
        )
    except TelegramAuthStateError as e:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "wrong_state",
                "message": f"O login não está esperando a senha (estado atual: {e.actual}).",
            },
        )
    except TelegramAuthError as e:
        _raise(e)


@router.post("/logout", response_model=AuthStatusResponse)
async def logout():
    try:
        return await telegram_auth_service.logout()
    except TelegramAuthBusyError:
        raise HTTPException(
            status_code=409,
            detail={"code": "auth_busy", "message": "Outra operação de login está em andamento."},
        )
