from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.product_interest import ProductInterest
from app.models.promotion_match import PromotionMatch
from app.models.telegram_message import TelegramMessage
from app.schemas.match import MatchDetailResponse

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.get("", response_model=list[MatchDetailResponse])
def list_matches(
    interest_id: int | None = Query(None),
    alerted: bool | None = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = (
        select(
            PromotionMatch,
            TelegramMessage.chat_name,
            TelegramMessage.text,
            ProductInterest.nome_produto,
        )
        .join(TelegramMessage, PromotionMatch.message_id == TelegramMessage.id)
        .join(ProductInterest, PromotionMatch.interest_id == ProductInterest.id)
        .order_by(desc(PromotionMatch.created_at))
    )

    if interest_id is not None:
        query = query.where(PromotionMatch.interest_id == interest_id)
    if alerted is not None:
        query = query.where(PromotionMatch.alerted == alerted)

    query = query.offset(skip).limit(limit)
    rows = db.execute(query).all()

    results = []
    for match, chat_name, text, nome_produto in rows:
        chat_id = None
        message_id = None
        for m2 in db.query(TelegramMessage).filter(TelegramMessage.id == match.message_id):
            chat_id = m2.chat_id
            message_id = m2.message_id
            break

        link = ""
        if chat_id and message_id:
            chat_str = str(chat_id)
            if chat_str.startswith("-100"):
                chat_str = chat_str[4:]
            elif chat_str.startswith("-"):
                chat_str = chat_str[1:]
            link = f"https://t.me/c/{chat_str}/{message_id}"

        results.append(
            MatchDetailResponse(
                id=match.id,
                message_id=match.message_id,
                interest_id=match.interest_id,
                preco_encontrado=match.preco_encontrado,
                score=match.score,
                raw_text_snippet=match.raw_text_snippet,
                alerted=match.alerted,
                alerted_at=match.alerted_at,
                created_at=match.created_at,
                chat_name=chat_name,
                message_text=text,
                message_link=link,
                produto_nome=nome_produto,
            )
        )

    return results
