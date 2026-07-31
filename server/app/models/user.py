from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

PAPEL_OWNER = "owner"
PAPEL_VIEWER = "viewer"
PAPEIS = (PAPEL_OWNER, PAPEL_VIEWER)


class User(Base, TimestampMixin):
    """Usuário do painel. Não há cadastro aberto: só o owner cria usuários."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    nome: Mapped[str] = mapped_column(String(120))
    senha_hash: Mapped[str] = mapped_column(String(255))
    papel: Mapped[str] = mapped_column(String(20), default=PAPEL_VIEWER)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    trocar_senha: Mapped[bool] = mapped_column(Boolean, default=False)
    ultimo_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now(),
        server_default=func.now(),
    )

    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def is_owner(self) -> bool:
        return self.papel == PAPEL_OWNER


class UserSession(Base):
    """Sessão opaca. O cookie carrega o token cru; aqui fica só o hash dele."""

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ultimo_uso_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user: Mapped[User] = relationship(back_populates="sessions")
