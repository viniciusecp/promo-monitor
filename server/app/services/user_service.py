"""Gestão de usuários do painel — só o owner chega aqui."""

from __future__ import annotations

from app.core.exceptions import AuthError, UserNotFoundError
from app.core.logging import logger
from app.core.security import (
    hash_password,
    normalize_email,
    validate_password_strength,
)
from app.models.user import PAPEL_OWNER, User
from app.repositories.user_repo import SessionRepository, UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, user_repo: UserRepository, session_repo: SessionRepository) -> None:
        self.users = user_repo
        self.sessions = session_repo

    def list(self) -> list[User]:
        return self.users.list_all()

    def create(self, data: UserCreate) -> User:
        email = normalize_email(str(data.email))
        if self.users.get_by_email(email) is not None:
            raise AuthError("email_taken", "Já existe um usuário com este e-mail.")

        erro = validate_password_strength(data.senha)
        if erro:
            raise AuthError("password_weak", erro)

        user = self.users.create(
            email=email,
            nome=data.nome.strip(),
            senha_hash=hash_password(data.senha),
            papel=data.papel,
            ativo=True,
            trocar_senha=True,
        )
        logger.info("user_created", user_id=user.id, email=user.email, papel=user.papel)
        return user

    def update(self, user_id: int, data: UserUpdate, actor: User) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        campos = data.model_dump(exclude_unset=True)

        perde_owner = (
            campos.get("papel") not in (None, PAPEL_OWNER) and user.papel == PAPEL_OWNER
        ) or campos.get("ativo") is False
        if perde_owner:
            self._assert_nao_e_ultimo_owner(user)

        revogar = "papel" in campos or campos.get("ativo") is False

        atualizado = self.users.update(user_id, **campos)
        if revogar:
            self.sessions.delete_by_user(user_id)

        logger.info(
            "user_updated",
            user_id=user_id,
            por=actor.id,
            campos=sorted(campos),
            sessoes_revogadas=revogar,
        )
        return atualizado

    def delete(self, user_id: int, actor: User) -> None:
        user = self.users.get(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        if user.id == actor.id:
            raise AuthError("self_delete", "Você não pode excluir a própria conta.")

        self._assert_nao_e_ultimo_owner(user)

        self.sessions.delete_by_user(user_id)
        self.users.delete(user_id)
        logger.info("user_deleted", user_id=user_id, por=actor.id)

    def reset_password(self, user_id: int, senha: str, actor: User) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        erro = validate_password_strength(senha)
        if erro:
            raise AuthError("password_weak", erro)

        atualizado = self.users.update(
            user_id,
            senha_hash=hash_password(senha),
            trocar_senha=True,
        )
        self.sessions.delete_by_user(user_id)
        logger.info("user_password_reset", user_id=user_id, por=actor.id)
        return atualizado

    def _assert_nao_e_ultimo_owner(self, user: User) -> None:
        """Sem isto o painel fica sem ninguém capaz de administrá-lo, e como
        não há auto-cadastro a única saída seria editar o SQLite na mão.
        """
        if user.papel != PAPEL_OWNER or not user.ativo:
            return
        if self.users.count_active_owners(excluding_id=user.id) == 0:
            raise AuthError(
                "last_owner",
                "Este é o único administrador ativo. Promova outro usuário antes.",
            )
