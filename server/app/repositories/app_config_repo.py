from sqlalchemy.orm import Session

from app.models.app_config import AppConfig
from app.repositories.base import BaseRepository


class AppConfigRepository(BaseRepository[AppConfig]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, AppConfig)

    def get_or_create(self) -> AppConfig:
        config = self.get(1)
        if config is None:
            config = self.create(alert_target=None)
        return config

    def set_target(self, value: str | None) -> AppConfig:
        config = self.get_or_create()
        config.alert_target = value
        self.db.commit()
        self.db.refresh(config)
        return config
