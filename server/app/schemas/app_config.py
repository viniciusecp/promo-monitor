from datetime import datetime

from pydantic import BaseModel, Field


class SettingsUpdate(BaseModel):
    # `alert_target` não entra aqui de propósito: o destino é gravado só pelo
    # handler `/start` do bot, que é a única forma de garantir que o bot
    # consegue escrever no chat escolhido. Semântica parcial preservada (o
    # service usa `exclude_unset`): campo ausente significa "não mexe" e `null`
    # explícito significa "limpa".
    telegram_bot_token: str | None = Field(None, max_length=255)


class SettingsResponse(BaseModel):
    alert_target: str | None
    updated_at: datetime
    telegram_bot_token_set: bool
    telegram_bot_token_masked: str | None
    bot_connected: bool
    bot_username: str | None
    bot_last_error: str | None

    model_config = {"from_attributes": True}


class AlertTestResponse(BaseModel):
    ok: bool
    error: str | None = None
