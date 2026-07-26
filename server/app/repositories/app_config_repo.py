from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.app_config import AppConfig
from app.repositories.base import BaseRepository


class AppConfigRepository(BaseRepository[AppConfig]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, AppConfig)

    def get_or_create(self) -> AppConfig:
        config = self.get(1)
        if config is None:
            # Semeia o token do .env só na criação da linha. Depois disso o
            # banco manda: limpar o campo pelo painel desativa o bot de vez, em
            # vez de ressuscitar o valor do .env no próximo restart.
            config = self.create(
                alert_target=None,
                telegram_bot_token=settings.telegram_bot_token or None,
            )
        return config

    def set_target(self, value: str | None) -> AppConfig:
        return self.set_fields(alert_target=value)

    def set_fields(self, **fields) -> AppConfig:
        config = self.get_or_create()
        for name, value in fields.items():
            setattr(config, name, value)
        self.db.commit()
        self.db.refresh(config)
        return config
