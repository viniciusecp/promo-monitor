"""Login do painel (e-mail + senha)."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.api.deps import (
    clear_session_cookie,
    client_ip,
    get_auth_service,
    get_current_user,
    set_session_cookie,
)
from app.core.config import settings
from app.core.exceptions import AuthError
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LogoutResponse, SessionResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

_STATUS_BY_CODE = {
    "credentials_invalid": 401,
    "not_authenticated": 401,
    "session_expired": 401,
    "password_invalid": 400,
    "password_weak": 400,
    "password_reused": 400,
    "user_disabled": 403,
    "too_many_attempts": 429,
}


def _raise(exc: AuthError) -> None:
    headers = {"Retry-After": str(exc.retry_after)} if exc.retry_after else None
    raise HTTPException(
        status_code=_STATUS_BY_CODE.get(exc.code, 400),
        detail={
            "code": exc.code,
            "message": exc.message,
            "retry_after": exc.retry_after,
        },
        headers=headers,
    )


@router.post("/login", response_model=SessionResponse)
def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    try:
        user, token = service.login(
            email=str(data.email),
            senha=data.senha,
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except AuthError as exc:
        _raise(exc)

    set_session_cookie(response, token)
    return SessionResponse(user=user)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    token = request.cookies.get(settings.auth_cookie_name)
    if token:
        service.logout(token)
    clear_session_cookie(response)
    return LogoutResponse()


@router.get("/me", response_model=SessionResponse)
def me(user: User = Depends(get_current_user)):
    return SessionResponse(user=user)


@router.post("/password", response_model=SessionResponse)
def change_password(
    data: ChangePasswordRequest,
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    try:
        service.change_password(user, data.senha_atual, data.senha_nova)
    except AuthError as exc:
        _raise(exc)

    token = service.open_session(user, ip=client_ip(request), user_agent="troca-de-senha")
    set_session_cookie(response, token)
    return SessionResponse(user=user)
