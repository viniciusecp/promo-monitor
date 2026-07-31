"""Gestão de usuários. Router inteiro restrito a `owner`."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_owner
from app.core.exceptions import AuthError, UserNotFoundError
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repo import SessionRepository, UserRepository
from app.schemas.user import UserCreate, UserPasswordReset, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(require_owner)],
)

_STATUS_BY_CODE = {
    "email_taken": 409,
    "last_owner": 409,
    "self_delete": 409,
    "password_weak": 400,
}


def get_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db), SessionRepository(db))


def _raise(exc: AuthError) -> None:
    raise HTTPException(
        status_code=_STATUS_BY_CODE.get(exc.code, 400),
        detail={"code": exc.code, "message": exc.message},
    )


@router.get("", response_model=list[UserResponse])
def list_users(service: UserService = Depends(get_service)):
    return service.list()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, service: UserService = Depends(get_service)):
    try:
        return service.create(data)
    except AuthError as exc:
        _raise(exc)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    actor: User = Depends(require_owner),
    service: UserService = Depends(get_service),
):
    try:
        return service.update(user_id, data, actor)
    except UserNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={"code": "user_not_found", "message": "Usuário não encontrado."},
        )
    except AuthError as exc:
        _raise(exc)


@router.post("/{user_id}/password", response_model=UserResponse)
def reset_password(
    user_id: int,
    data: UserPasswordReset,
    actor: User = Depends(require_owner),
    service: UserService = Depends(get_service),
):
    try:
        return service.reset_password(user_id, data.senha, actor)
    except UserNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={"code": "user_not_found", "message": "Usuário não encontrado."},
        )
    except AuthError as exc:
        _raise(exc)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    actor: User = Depends(require_owner),
    service: UserService = Depends(get_service),
):
    try:
        service.delete(user_id, actor)
    except UserNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={"code": "user_not_found", "message": "Usuário não encontrado."},
        )
    except AuthError as exc:
        _raise(exc)
