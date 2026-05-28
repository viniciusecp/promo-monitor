from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, db: Session, model: type[ModelT]) -> None:
        self.db = db
        self.model = model

    def create(self, **kwargs: Any) -> ModelT:
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def get(self, id: int) -> ModelT | None:
        return self.db.get(self.model, id)

    def list(self, skip: int = 0, limit: int = 100, **filters: Any) -> list[ModelT]:
        query = select(self.model)
        for field, value in filters.items():
            if value is not None:
                column = getattr(self.model, field, None)
                if column is not None:
                    query = query.where(column == value)
        query = query.offset(skip).limit(limit)
        return list(self.db.scalars(query).all())

    def update(self, id: int, **kwargs: Any) -> ModelT | None:
        instance = self.get(id)
        if instance is None:
            return None
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, id: int) -> bool:
        instance = self.get(id)
        if instance is None:
            return False
        self.db.delete(instance)
        self.db.commit()
        return True
