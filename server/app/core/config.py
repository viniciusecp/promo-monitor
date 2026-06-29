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
    telegram_bot_token: str | None = None
    telegram_bot_session_file: str = str(SESSION_DIR / "bot.session")

    database_url: str = f"sqlite:///{DATA_DIR / 'promobot.db'}"

    match_score_threshold: float = 0.6

    # Validação dos candidatos do matcher por LLM (via LangChain + OpenRouter).
    # Sem openrouter_api_key, a validação fica desativada (comportamento atual).
    openrouter_api_key: str | None = None
    llm_validation_enabled: bool = True
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "openai/gpt-4o-mini"
    llm_timeout: float = 20.0

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    def model_post_init(self, __context) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SESSION_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
