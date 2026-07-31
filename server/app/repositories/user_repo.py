from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.core.security import normalize_email
from app.models.user import PAPEL_OWNER, User, UserSession
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, User)

    def get_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == normalize_email(email))
        return self.db.scalars(query).first()

    def list_all(self) -> list[User]:
        query = select(User).order_by(User.nome, User.id)
        return list(self.db.scalars(query).all())

    def count_all(self) -> int:
        return self.count_where()

    def count_active_owners(self, excluding_id: int | None = None) -> int:
        """Sustenta a trava do último owner (ver `UserService`)."""
        criteria = [User.papel == PAPEL_OWNER, User.ativo.is_(True)]
        if excluding_id is not None:
            criteria.append(User.id != excluding_id)
        return self.count_where(*criteria)


class SessionRepository(BaseRepository[UserSession]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, UserSession)

    def get_by_token_hash(self, token_hash: str) -> UserSession | None:
        # joinedload: isto roda em toda request autenticada.
        query = (
            select(UserSession)
            .options(joinedload(UserSession.user))
            .where(UserSession.token_hash == token_hash)
        )
        return self.db.scalars(query).first()

    def delete_by_token_hash(self, token_hash: str) -> None:
        self.db.execute(
            delete(UserSession).where(UserSession.token_hash == token_hash)
        )
        self.db.commit()

    def delete_by_user(self, user_id: int) -> int:
        result = self.db.execute(
            delete(UserSession).where(UserSession.user_id == user_id)
        )
        self.db.commit()
        return result.rowcount or 0

    def delete_expired(self, now: datetime) -> int:
        result = self.db.execute(
            delete(UserSession).where(UserSession.expira_em < now)
        )
        self.db.commit()
        return result.rowcount or 0

    def touch(self, session: UserSession, agora: datetime, expira_em: datetime) -> None:
        session.ultimo_uso_em = agora
        session.expira_em = expira_em
        self.db.commit()
