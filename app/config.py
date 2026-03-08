from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    SECRET_KEY: str = "local-dev-secret"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite+aiosqlite:///./bot.db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40

    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_REQUIRED: bool = False

    JWT_PRIVATE_KEY: str = "dev-private-key"
    JWT_PUBLIC_KEY: str = "dev-public-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 30

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    MT5_ENCRYPTION_KEY_ID: str = "trading/mt5/encryption-key"
    AI_SERVICE_URL: str = "http://localhost:8001"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @staticmethod
    def _backend_dir() -> Path:
        return Path(__file__).resolve().parents[1]

    @classmethod
    def _sqlite_async_url(cls) -> str:
        return f"sqlite+aiosqlite:///{cls._backend_dir() / 'bot.db'}"

    @classmethod
    def _sqlite_sync_url(cls) -> str:
        return f"sqlite:///{cls._backend_dir() / 'bot.db'}"

    def is_production(self) -> bool:
        return self.APP_ENV.lower() in {"prod", "production"}

    @staticmethod
    def _normalize_postgres_url(url: str, async_mode: bool) -> str:
        normalized = url.strip()
        if normalized.startswith("postgres://"):
            normalized = "postgresql://" + normalized[len("postgres://") :]

        if async_mode:
            if normalized.startswith("postgresql+psycopg2://"):
                return "postgresql+asyncpg://" + normalized[len("postgresql+psycopg2://") :]
            if normalized.startswith("postgresql://"):
                return "postgresql+asyncpg://" + normalized[len("postgresql://") :]
        else:
            if normalized.startswith("postgresql+asyncpg://"):
                return "postgresql+psycopg2://" + normalized[len("postgresql+asyncpg://") :]
            if normalized.startswith("postgresql://"):
                return "postgresql+psycopg2://" + normalized[len("postgresql://") :]

        return normalized

    @property
    def database_url_async(self) -> str:
        if self.is_production():
            return self._normalize_postgres_url(self.DATABASE_URL, async_mode=True)
        return self._sqlite_async_url()

    @property
    def database_url_sync(self) -> str:
        if self.is_production():
            return self._normalize_postgres_url(self.DATABASE_URL, async_mode=False)
        return self._sqlite_sync_url()


settings = Settings()

