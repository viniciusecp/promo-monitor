"""Dependências de autenticação e o helper do cookie de sessão."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthError
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repo import SessionRepository, UserRepository
from app.services.auth_service import AuthService

RENEW_FLAG = "_pm_renew_session"


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db), SessionRepository(db))


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=settings.auth_session_days * 86400,
        httponly=True,
        samesite="lax",
        secure=settings.auth_cookie_secure,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_cookie_name,
        httponly=True,
        samesite="lax",
        secure=settings.auth_cookie_secure,
        path="/",
    )


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "desconhecido"


def get_current_user(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> User:
    token = request.cookies.get(settings.auth_cookie_name)
    if not token:
        raise HTTPException(
            status_code=401,
            detail={"code": "not_authenticated", "message": "Faça login para continuar."},
        )

    try:
        user, renovada = service.resolve_session(token)
    except AuthError as exc:
        clear_session_cookie(response)
        raise HTTPException(
            status_code=401,
            detail={"code": exc.code, "message": exc.message},
        )

    if renovada:
        setattr(request.state, RENEW_FLAG, token)

    return user


def require_user(user: User = Depends(get_current_user)) -> User:
    return user


def require_owner(user: User = Depends(get_current_user)) -> User:
    if not user.is_owner:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "forbidden",
                "message": "Esta ação é restrita a administradores.",
            },
        )
    return user
