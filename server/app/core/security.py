"""Primitivas de autenticação: hash de senha, tokens de sessão e rate limit."""

from __future__ import annotations

import hashlib
import secrets
import time
from dataclasses import dataclass, field

from pwdlib import PasswordHash

_password_hash = PasswordHash.recommended()

MIN_PASSWORD_LENGTH = 10
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 300

_DUMMY_HASH = _password_hash.hash("promo-monitor-dummy-password")


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, senha_hash: str | None) -> bool:
    """`senha_hash=None` gasta o mesmo tempo de uma verificação real."""
    if not senha_hash:
        _password_hash.verify(password, _DUMMY_HASH)
        return False
    try:
        return _password_hash.verify(password, senha_hash)
    except Exception:
        return False


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Só o hash vai para o banco — um vazamento não vira sessão válida.

    SHA-256 sem KDF basta aqui, ao contrário de senha: são 256 bits de entropia,
    não há o que adivinhar por força bruta.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_password_strength(password: str) -> str | None:
    """Devolve a mensagem de erro, ou None se a senha serve."""
    minimo = MIN_PASSWORD_LENGTH
    if len(password) < minimo:
        return f"A senha precisa ter pelo menos {minimo} caracteres."
    return None


@dataclass
class _Attempt:
    failures: int = 0
    blocked_until: float = 0.0
    last_seen: float = 0.0


@dataclass
class LoginThrottle:
    """Bloqueio progressivo por (e-mail, IP), mantido em memória."""

    max_attempts: int = MAX_LOGIN_ATTEMPTS
    lockout_seconds: int = LOCKOUT_SECONDS
    _attempts: dict[tuple[str, str], _Attempt] = field(default_factory=dict)

    def retry_after(self, email: str, ip: str) -> int:
        """Segundos restantes de bloqueio; 0 quando está liberado."""
        self._prune()
        entry = self._attempts.get((normalize_email(email), ip))
        if entry is None:
            return 0
        restante = entry.blocked_until - time.monotonic()
        return int(restante) + 1 if restante > 0 else 0

    def register_failure(self, email: str, ip: str) -> int:
        """Devolve o bloqueio resultante em segundos (0 se ainda não bloqueou)."""
        self._prune()
        key = (normalize_email(email), ip)
        entry = self._attempts.setdefault(key, _Attempt())
        entry.failures += 1
        entry.last_seen = time.monotonic()
        if entry.failures >= self.max_attempts:
            excedente = entry.failures - self.max_attempts
            espera = min(self.lockout_seconds * (2**excedente), 3600)
            entry.blocked_until = time.monotonic() + espera
            return espera
        return 0

    def reset(self, email: str, ip: str) -> None:
        self._attempts.pop((normalize_email(email), ip), None)

    def _prune(self) -> None:
        agora = time.monotonic()
        limite = max(self.lockout_seconds, 3600) * 2
        vencidas = [
            key
            for key, entry in self._attempts.items()
            if entry.blocked_until < agora and agora - entry.last_seen > limite
        ]
        for key in vencidas:
            del self._attempts[key]


login_throttle = LoginThrottle()
