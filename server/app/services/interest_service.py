from app.core.exceptions import InterestNotFoundError
from app.repositories.interest_repo import InterestRepository
from app.schemas.interest import InterestCreate, InterestUpdate


class InterestService:
    def __init__(self, repo: InterestRepository) -> None:
        self.repo = repo

    def create(self, data: InterestCreate) -> dict:
        interest = self.repo.create(**data.model_dump())
        return self._to_dict(interest)

    def get(self, interest_id: int) -> dict:
        interest = self.repo.get(interest_id)
        if interest is None:
            raise InterestNotFoundError(interest_id)
        return self._to_dict(interest)

    def list(self, ativo: bool | None = None, skip: int = 0, limit: int = 100) -> list[dict]:
        filters = {}
        if ativo is not None:
            filters["ativo"] = ativo
        interests = self.repo.list(skip=skip, limit=limit, **filters)
        return [self._to_dict(i) for i in interests]

    def update(self, interest_id: int, data: InterestUpdate) -> dict:
        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        if not updates:
            return self.get(interest_id)
        interest = self.repo.update(interest_id, **updates)
        if interest is None:
            raise InterestNotFoundError(interest_id)
        return self._to_dict(interest)

    def delete(self, interest_id: int) -> None:
        if not self.repo.delete(interest_id):
            raise InterestNotFoundError(interest_id)

    def _to_dict(self, interest) -> dict:
        return {
            "id": interest.id,
            "nome_produto": interest.nome_produto,
            "preco_maximo": interest.preco_maximo,
            "limiar_match": interest.limiar_match,
            "palavras_chave": interest.palavras_chave,
            "palavras_excluidas": interest.palavras_excluidas,
            "ativo": interest.ativo,
            "created_at": interest.created_at,
            "updated_at": interest.updated_at,
        }
