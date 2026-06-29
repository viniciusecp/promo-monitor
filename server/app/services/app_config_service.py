from app.repositories.app_config_repo import AppConfigRepository
from app.schemas.app_config import SettingsUpdate


class AppConfigService:
    def __init__(self, repo: AppConfigRepository) -> None:
        self.repo = repo

    def get(self) -> dict:
        config = self.repo.get_or_create()
        return self._to_dict(config)

    def update(self, data: SettingsUpdate) -> dict:
        target = data.alert_target
        if target is not None:
            target = target.strip() or None
        config = self.repo.set_target(target)
        return self._to_dict(config)

    def _to_dict(self, config) -> dict:
        return {
            "alert_target": config.alert_target,
            "updated_at": config.updated_at,
        }
