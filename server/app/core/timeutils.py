"""Helpers de data/hora.

Contexto importante: as colunas `DateTime(timezone=True)` deste projeto guardam
na prática **naive-UTC**. No SQLite o bind processor do SQLAlchemy serializa
apenas os campos de wall-clock do datetime e descarta o tzinfo — ele *não*
converte para UTC antes. Como o código sempre grava com `datetime.now(timezone.utc)`,
o que fica no banco é wall-clock UTC sem offset.

Consequência: qualquer datetime usado em comparação (filtro de período, por
exemplo) precisa ser normalizado para UTC e ter o tzinfo removido, senão a
comparação mistura fusos silenciosamente.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config import settings


def utcnow_naive() -> datetime:
    """Agora, em UTC, sem tzinfo — no formato que as colunas guardam."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(value: datetime) -> datetime:
    """Normaliza para UTC e remove o tzinfo. Naive é assumido como já UTC."""
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def resolve_timezone(name: str | None) -> ZoneInfo:
    """Resolve um IANA tz name, caindo para o default da app e depois UTC.

    Degrada em vez de levantar: um `tz` inválido vindo do browser não deve
    derrubar a request.
    """
    for candidate in (name, settings.app_timezone, "UTC"):
        if not candidate:
            continue
        try:
            return ZoneInfo(candidate)
        except (ZoneInfoNotFoundError, ValueError):
            continue
    return ZoneInfo("UTC")
