from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class ProductInterest(Base, TimestampMixin):
    __tablename__ = "product_interests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome_produto: Mapped[str] = mapped_column(String(255), nullable=False)
    preco_maximo: Mapped[float | None] = mapped_column(Float, nullable=True)
    limiar_match: Mapped[float | None] = mapped_column(Float, nullable=True)
    palavras_chave: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    palavras_excluidas: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now(),
        server_default=func.now(),
    )

    matches: Mapped[list["PromotionMatch"]] = relationship(
        "PromotionMatch", back_populates="interest", cascade="all, delete-orphan"
    )
