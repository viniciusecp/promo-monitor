from datetime import datetime

from pydantic import BaseModel, Field


class SettingsUpdate(BaseModel):
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
