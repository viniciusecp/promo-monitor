from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.telegram_message import TelegramMessage
from app.schemas.message import MessageResponse

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.get("", response_model=list[MessageResponse])
def list_messages(
    chat_id: int | None = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = select(TelegramMessage).order_by(desc(TelegramMessage.created_at))
    if chat_id is not None:
        query = query.where(TelegramMessage.chat_id == chat_id)
    query = query.offset(skip).limit(limit)
    return list(db.scalars(query).all())
