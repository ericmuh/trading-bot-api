from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str
    app_encryption_key: str | None
    database_path: str


def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "dev"),
        app_encryption_key=os.getenv("APP_ENCRYPTION_KEY"),
        database_path=os.getenv("DATABASE_PATH", "./bot.db"),
    )
