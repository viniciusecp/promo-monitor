from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product_interest import ProductInterest
from app.repositories.base import BaseRepository


class InterestRepository(BaseRepository[ProductInterest]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ProductInterest)

    def list_active(self) -> list[ProductInterest]:
        # Query própria em vez de `self.list(ativo=True)`: o BaseRepository
        # aplica limit=100 por padrão, e este método alimenta o worker do
        # Telegram — truncar aqui faria os interesses excedentes pararem de
        # ser avaliados silenciosamente. Não é uma listagem paginada.
        query = (
            select(ProductInterest)
            .where(ProductInterest.ativo.is_(True))
            .order_by(ProductInterest.id)
        )
        return list(self.db.scalars(query).all())
