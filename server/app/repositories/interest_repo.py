from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product_interest import ProductInterest
from app.repositories.base import BaseRepository


class InterestRepository(BaseRepository[ProductInterest]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ProductInterest)

    def list_active(self) -> list[ProductInterest]:
        query = (
            select(ProductInterest)
            .where(ProductInterest.ativo.is_(True))
            .order_by(ProductInterest.id)
        )
        return list(self.db.scalars(query).all())
