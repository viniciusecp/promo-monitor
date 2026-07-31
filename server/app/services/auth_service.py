"""Autenticação do painel: login, sessão persistente e troca de senha.

Sessão opaca em vez de JWT, de propósito. O que decide é a **revogação**:
desativar ou excluir um usuário precisa derrubar o acesso dele na hora, e um
JWT só expira. O custo é um SELECT indexado por request — irrelevante num
SQLite com um punhado de usuários.
"""

from __future__ import annotations

from datetime import timedelta

from app.core.config import settings
from app.core.exceptions import AuthError
from app.core.logging import logger
from app.core.security import (
    generate_session_token,
    hash_password,
    hash_token,
    login_throttle,
    normalize_email,
    validate_password_strength,
    verify_password,
)
from app.core.timeutils import utcnow_naive
from app.models.user import PAPEL_OWNER, User
from app.repositories.user_repo import SessionRepository, UserRepository

_RENOVA_APOS = timedelta(hours=1)


class AuthService:
    def __init__(self, user_repo: UserRepository, session_repo: SessionRepository) -> None:
        self.users = user_repo
        self.sessions = session_repo

    # --- login / logout ---

    def login(
        self,
        email: str,
        senha: str,
        ip: str,
        user_agent: str | None = None,
    ) -> tuple[User, str]:
        """Valida credenciais e abre uma sessão. Devolve (usuário, token cru)."""
        bloqueio = login_throttle.retry_after(email, ip)
        if bloqueio:
            raise AuthError(
                "too_many_attempts",
                "Muitas tentativas de login. Tente novamente mais tarde.",
                retry_after=bloqueio,
            )

        user = self.users.get_by_email(email)
        senha_ok = verify_password(senha, user.senha_hash if user else None)

        if user is None or not senha_ok:
            espera = login_throttle.register_failure(email, ip)
            logger.warning("login_failed", email=normalize_email(email), ip=ip)
            if espera:
                raise AuthError(
                    "too_many_attempts",
                    "Muitas tentativas de login. Tente novamente mais tarde.",
                    retry_after=espera,
                )
            raise AuthError("credentials_invalid", "E-mail ou senha incorretos.")

        if not user.ativo:
            raise AuthError("user_disabled", "Este acesso foi desativado.")

        login_throttle.reset(email, ip)

        token = self.open_session(user, ip=ip, user_agent=user_agent)
        logger.info("login_ok", user_id=user.id, email=user.email, papel=user.papel)
        return user, token

    def open_session(self, user: User, ip: str = "", user_agent: str | None = None) -> str:
        agora = utcnow_naive()
        token = generate_session_token()
        self.sessions.create(
            user_id=user.id,
            token_hash=hash_token(token),
            criada_em=agora,
            expira_em=agora + timedelta(days=settings.auth_session_days),
            ultimo_uso_em=agora,
            user_agent=(user_agent or "")[:255] or None,
            ip=ip[:64] or None,
        )
        self.users.update(user.id, ultimo_login=agora)
        return token

    def logout(self, token: str) -> None:
        self.sessions.delete_by_token_hash(hash_token(token))

    def logout_all(self, user_id: int) -> int:
        return self.sessions.delete_by_user(user_id)

    # --- sessão ---

    def resolve_session(self, token: str) -> tuple[User, bool]:
        """Resolve o token do cookie.

        Devolve `(user, renovada)`. O `renovada` é o que faz a camada HTTP
        reemitir o `Set-Cookie`: estender só a linha do banco deixaria o cookie
        expirar antes no navegador, e o usuário cairia no login mesmo usando o
        painel todo dia — exatamente o sintoma que o login persistente evita.
        """
        session = self.sessions.get_by_token_hash(hash_token(token))
        if session is None:
            raise AuthError("not_authenticated", "Sessão inválida ou expirada.")

        agora = utcnow_naive()
        if session.expira_em <= agora:
            self.sessions.delete_by_token_hash(session.token_hash)
            raise AuthError("session_expired", "Sua sessão expirou. Entre de novo.")

        user = session.user
        if user is None or not user.ativo:
            self.sessions.delete_by_token_hash(session.token_hash)
            raise AuthError("user_disabled", "Este acesso foi desativado.")

        renovada = False
        if agora - session.ultimo_uso_em >= _RENOVA_APOS:
            self.sessions.touch(
                session,
                agora,
                agora + timedelta(days=settings.auth_session_days),
            )
            renovada = True

        return user, renovada

    def purge_expired(self) -> int:
        return self.sessions.delete_expired(utcnow_naive())

    # --- senha ---

    def change_password(self, user: User, senha_atual: str, senha_nova: str) -> None:
        if not verify_password(senha_atual, user.senha_hash):
            raise AuthError("password_invalid", "A senha atual está incorreta.")

        erro = validate_password_strength(senha_nova)
        if erro:
            raise AuthError("password_weak", erro)

        if verify_password(senha_nova, user.senha_hash):
            raise AuthError("password_reused", "A nova senha precisa ser diferente da atual.")

        self.users.update(
            user.id,
            senha_hash=hash_password(senha_nova),
            trocar_senha=False,
        )
        self.sessions.delete_by_user(user.id)
        logger.info("password_changed", user_id=user.id)

    # --- bootstrap ---

    def seed_owner(self) -> None:
        """Cria o primeiro owner a partir do .env, só com a tabela vazia."""
        if self.users.count_all() > 0:
            return

        email = settings.auth_seed_email
        senha = settings.auth_seed_password
        if not email or not senha:
            logger.warning(
                "auth_no_users",
                hint="defina AUTH_SEED_EMAIL e AUTH_SEED_PASSWORD no server/.env",
            )
            return

        erro = validate_password_strength(senha)
        if erro:
            logger.error("auth_seed_password_weak", motivo=erro)
            return

        user = self.users.create(
            email=normalize_email(email),
            nome="Administrador",
            senha_hash=hash_password(senha),
            papel=PAPEL_OWNER,
            ativo=True,
            trocar_senha=True,
        )
        logger.info("auth_owner_seeded", user_id=user.id, email=user.email)
