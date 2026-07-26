from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.app_config_repo import AppConfigRepository
from app.schemas.app_config import AlertTestResponse, SettingsResponse, SettingsUpdate
from app.services.app_config_service import AppConfigService

router = APIRouter(prefix="/settings", tags=["Settings"])


def get_service(db: Session = Depends(get_db)) -> AppConfigService:
    repo = AppConfigRepository(db)
    return AppConfigService(repo)


@router.get("", response_model=SettingsResponse)
def get_settings(service: AppConfigService = Depends(get_service)):
    return service.get()


@router.put("", response_model=SettingsResponse)
async def update_settings(
    data: SettingsUpdate,
    service: AppConfigService = Depends(get_service),
):
    return await service.update(data)


@router.post("/alert/test", response_model=AlertTestResponse)
async def test_alert(service: AppConfigService = Depends(get_service)):
    return await service.send_test_alert()
