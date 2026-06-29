from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.models.product_interest import ProductInterest
from app.repositories.interest_repo import InterestRepository
from app.repositories.message_repo import MessageRepository
from app.services.matcher_service import composite_matcher

router = APIRouter(prefix="/matcher", tags=["Matcher"])


class PreviewRequest(BaseModel):
    interest_id: int | None = None
    nome_produto: str | None = Field(None, min_length=1, max_length=255)
    palavras_chave: list[str] = Field(default_factory=list)
    palavras_excluidas: list[str] = Field(default_factory=list)
    preco_maximo: float | None = Field(None, ge=0)
    limiar: float | None = Field(None, ge=0, le=1)
    limit: int = Field(500, ge=1, le=5000)


class PreviewItem(BaseModel):
    message_id: int
    chat_name: str | None
    score: float
    breakdown: dict[str, float]
    preco: float | None
    snippet: str


class PreviewResponse(BaseModel):
    threshold: float
    total_scanned: int
    total_matched: int
    items: list[PreviewItem]


@router.post("/preview", response_model=PreviewResponse)
def preview(data: PreviewRequest, db: Session = Depends(get_db)) -> PreviewResponse:
    if data.interest_id is not None:
        interest = InterestRepository(db).get(data.interest_id)
        if interest is None:
            raise HTTPException(status_code=404, detail="Interesse não encontrado")
    else:
        if not data.nome_produto:
            raise HTTPException(
                status_code=422,
                detail="Informe interest_id ou nome_produto para o preview",
            )
        interest = ProductInterest(
            nome_produto=data.nome_produto,
            preco_maximo=data.preco_maximo,
            limiar_match=data.limiar,
            palavras_chave=data.palavras_chave,
            palavras_excluidas=data.palavras_excluidas,
            ativo=True,
        )

    threshold = data.limiar or interest.limiar_match or settings.match_score_threshold

    messages = MessageRepository(db).list_recent(data.limit)
    items: list[PreviewItem] = []
    for msg in messages:
        if not msg.text:
            continue
        score, prices, breakdown, _ = composite_matcher.match(msg.text, interest)
        if score < threshold:
            continue
        preco = min(prices) if prices else None
        if interest.preco_maximo and preco and preco > interest.preco_maximo:
            continue
        items.append(
            PreviewItem(
                message_id=msg.id,
                chat_name=msg.chat_name,
                score=round(score, 4),
                breakdown={k: round(v, 4) for k, v in breakdown.items()},
                preco=preco,
                snippet=msg.text[:300],
            )
        )

    items.sort(key=lambda i: i.score, reverse=True)
    return PreviewResponse(
        threshold=threshold,
        total_scanned=len(messages),
        total_matched=len(items),
        items=items,
    )
