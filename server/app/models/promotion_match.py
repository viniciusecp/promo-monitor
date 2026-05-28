from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class PromotionMatch(Base, TimestampMixin):
    __tablename__ = "promotion_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("telegram_messages.id"), nullable=False)
    interest_id: Mapped[int] = mapped_column(Integer, ForeignKey("product_interests.id"), nullable=False)
    preco_encontrado: Mapped[float | None] = mapped_column(Float, nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    raw_text_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    alerted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alerted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    message: Mapped["TelegramMessage"] = relationship(
        "TelegramMessage", back_populates="matches"
    )
    interest: Mapped["ProductInterest"] = relationship(
        "ProductInterest", back_populates="matches"
    )
