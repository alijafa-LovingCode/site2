"""
Central application configuration.

All configurable values are read from environment variables so that
nothing sensitive is ever hard-coded in source code. See .env.example
for the full list of supported variables.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    database_url: str = "postgresql://postgres:postgres@localhost:5432/mehrsa_planner"
    secret_key: str = "insecure-dev-key-change-me"
    session_expire_minutes: int = 1440

    # Seed accounts (only used the first time the DB is initialized)
    admin_password: str = "96082362a"
    student_password: str = "mehrsa1234"

    # App
    app_env: str = "production"
    app_timezone: str = "Asia/Tehran"
    default_language: str = "fa"
    cors_origins: str = "*"

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_enabled: bool = False
    telegram_timezone: str = "Asia/Tehran"

    # AI
    gemini_api_key: str = ""
    openai_api_key: str = ""
    ai_provider: str = "none"  # "gemini" | "openai" | "none"

    # Chat
    chat_retention_hours: int = 24

    # Cycle tracker privacy
    cycle_admin_access: bool = False

    # Motivational messages
    message_cycle_length: int = 30

    # Backups
    backup_dir: str = "/app/backups"

    # Rate limiting
    login_rate_limit: str = "10/minute"

    @property
    def cors_origin_list(self) -> List[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
