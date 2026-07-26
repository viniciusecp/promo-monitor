from app.core.masking import mask_token
from app.database.session import SessionLocal
from app.repositories.app_config_repo import AppConfigRepository
from app.schemas.app_config import SettingsUpdate
from app.services.alert_service import _resolve_target
from app.telegram.bot import bot_manager


class AppConfigService:
    def __init__(self, repo: AppConfigRepository) -> None:
        self.repo = repo

    def get(self) -> dict:
        return self._to_dict(self.repo.get_or_create())

    async def update(self, data: SettingsUpdate) -> dict:
        # `exclude_unset` é o que dá semântica parcial ao PUT: o frontend manda
        # só o campo que mudou e o resto fica intacto.
        changes = data.model_dump(exclude_unset=True)

        if "telegram_bot_token" in changes:
            value = changes["telegram_bot_token"]
            changes["telegram_bot_token"] = (value.strip() or None) if value else None

        config = (
            self.repo.set_fields(**changes) if changes else self.repo.get_or_create()
        )

        if "telegram_bot_token" in changes:
            # Grava primeiro, aplica depois: se o token novo for inválido ele
            # continua salvo e o erro aparece em `bot_last_error`, dando ao
            # usuário a chance de corrigir sem reiniciar nada.
            await bot_manager.apply_token(config.telegram_bot_token, SessionLocal)

        return self._to_dict(config)

    async def send_test_alert(self) -> dict:
        config = self.repo.get_or_create()
        if not config.alert_target:
            return {"ok": False, "error": "Nenhum destino de alerta configurado."}

        client = bot_manager.get_client()
        if client is None or not client.is_connected():
            return {"ok": False, "error": "O bot não está conectado."}

        try:
            await client.send_message(
                _resolve_target(config.alert_target),
                "🔔 Teste de notificação do Promo Monitor. Está tudo certo!",
            )
            return {"ok": True, "error": None}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _to_dict(self, config) -> dict:
        bot = bot_manager.snapshot_for(config.telegram_bot_token)
        return {
            "alert_target": config.alert_target,
            "updated_at": config.updated_at,
            "telegram_bot_token_set": bool(config.telegram_bot_token),
            "telegram_bot_token_masked": mask_token(config.telegram_bot_token),
            "bot_connected": bot.connected,
            "bot_username": bot.username,
            "bot_last_error": bot.last_error,
        }
