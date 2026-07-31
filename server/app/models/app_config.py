from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class AppConfig(Base, TimestampMixin):
    __tablename__ = "app_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_target: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Token do bot de notificações. Configurado exclusivamente pelo painel
    # (PUT /settings). "Limpar o campo" significa desativado (sem alertas).
    telegram_bot_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now(),
        server_default=func.now(),
    )
