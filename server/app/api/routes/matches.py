from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.exceptions import MatchNotFoundError
from app.database.session import get_db
from app.repositories.interest_repo import InterestRepository
from app.repositories.match_repo import MatchRepository
from app.schemas.match import (
    MatchBulkReadResponse,
    MatchChatResponse,
    MatchFilterParams,
    MatchListQuery,
    MatchListResponse,
    MatchReadResponse,
    MatchStatsResponse,
)
from app.services.match_service import MatchService

router = APIRouter(prefix="/matches", tags=["Matches"])


def get_service(db: Session = Depends(get_db)) -> MatchService:
    return MatchService(MatchRepository(db), InterestRepository(db))


@router.get("", response_model=MatchListResponse)
def list_matches(
    query: Annotated[MatchListQuery, Query()],
    service: MatchService = Depends(get_service),
):
    return service.list(query, skip=query.skip, limit=query.limit)


# As rotas literais vêm antes de qualquer /{match_id} — aqui a contagem de
# segmentos já as distingue, mas manter a ordem evita surpresa se um
# GET /matches/{id} for adicionado depois.
@router.get("/stats", response_model=MatchStatsResponse)
def match_stats(
    tz: str | None = Query(None),
    service: MatchService = Depends(get_service),
):
    return service.stats(tz)


@router.get("/chats", response_model=list[MatchChatResponse])
def match_chats(service: MatchService = Depends(get_service)):
    return service.chats()


@router.post("/read-all", response_model=MatchBulkReadResponse)
def mark_all_read(
    filters: MatchFilterParams,
    service: MatchService = Depends(get_service),
):
    return MatchBulkReadResponse(updated=service.mark_all_read(filters))


@router.post("/{match_id}/read", response_model=MatchReadResponse)
def mark_read(match_id: int, service: MatchService = Depends(get_service)):
    try:
        return service.set_lido(match_id, True)
    except MatchNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{match_id}/unread", response_model=MatchReadResponse)
def mark_unread(match_id: int, service: MatchService = Depends(get_service)):
    try:
        return service.set_lido(match_id, False)
    except MatchNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
