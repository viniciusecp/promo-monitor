from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
SESSION_DIR = BASE_DIR / "session"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "promo-monitor"
    debug: bool = False
    log_level: str = "INFO"

    telegram_api_id: int
    telegram_api_hash: str
    telegram_phone: str
    telegram_session_file: str = str(SESSION_DIR / "telegram.session")

    database_url: str = f"sqlite:///{DATA_DIR / 'promobot.db'}"

    match_score_threshold: float = 0.6

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    def model_post_init(self, __context) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SESSION_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
