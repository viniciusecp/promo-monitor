from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.interest_repo import InterestRepository
from app.schemas.interest import InterestCreate, InterestResponse, InterestUpdate
from app.services.interest_service import InterestService
from app.workers.supervisor import supervisor

router = APIRouter(prefix="/interests", tags=["Interests"])


def get_service(db: Session = Depends(get_db)) -> InterestService:
    repo = InterestRepository(db)
    return InterestService(repo)


@router.get("", response_model=list[InterestResponse])
def list_interests(
    ativo: bool | None = None,
    skip: int = 0,
    limit: int = 100,
    service: InterestService = Depends(get_service),
):
    return service.list(ativo=ativo, skip=skip, limit=limit)


@router.post("", response_model=InterestResponse, status_code=201)
def create_interest(
    data: InterestCreate,
    background: BackgroundTasks,
    service: InterestService = Depends(get_service),
):
    result = service.create(data)
    background.add_task(supervisor.sync_interests)
    return result


@router.get("/{interest_id}", response_model=InterestResponse)
def get_interest(
    interest_id: int,
    service: InterestService = Depends(get_service),
):
    return service.get(interest_id)


@router.put("/{interest_id}", response_model=InterestResponse)
def update_interest(
    interest_id: int,
    data: InterestUpdate,
    background: BackgroundTasks,
    service: InterestService = Depends(get_service),
):
    result = service.update(interest_id, data)
    background.add_task(supervisor.sync_interests)
    return result


@router.delete("/{interest_id}", status_code=204)
def delete_interest(
    interest_id: int,
    background: BackgroundTasks,
    service: InterestService = Depends(get_service),
):
    service.delete(interest_id)
    background.add_task(supervisor.sync_interests)
