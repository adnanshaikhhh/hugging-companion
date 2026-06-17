# Application configuration loaded from environment / .env.
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for Hugging Companion.

    All values are loaded from environment variables (or a local .env file).
    Sensible defaults are provided so the app boots in a clean checkout.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="HUGGING_COMPANION_",
        extra="ignore",
    )

    app_name: str = "Hugging Companion"
    db_url: str = "sqlite:///./data/hugging_companion.db"
    log_level: str = "info"
    default_duration_min: int = 25

    # OpenAI is intentionally NOT prefixed — the conventional name wins.
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"

    @property
    def has_openai(self) -> bool:
        """Return True when an OpenAI key is configured."""
        return bool(self.openai_api_key and self.openai_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()