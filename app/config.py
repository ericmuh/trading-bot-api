from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    SECRET_KEY: str = "local-dev-secret"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite+aiosqlite:///./bot.db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40

    REDIS_URL: str = "redis://localhost:6379/0"

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


settings = Settings()

