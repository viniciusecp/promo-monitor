from datetime import datetime

from pydantic import BaseModel, Field


class SettingsUpdate(BaseModel):
    alert_target: str | None = Field(None, max_length=255)


class SettingsResponse(BaseModel):
    alert_target: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}
