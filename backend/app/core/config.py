"""Centralized Application Configuration for SentinelX."""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "SentinelX — Cross-Camera Vehicle Intelligence"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./sentinelx_dev.db"

    # Valkey / Cache
    VALKEY_URL: str = "redis://localhost:6379/0"

    # Sentinel Sandbox Ingestion
    SENTINEL_CATALOG_URL: str = "http://localhost:8000/api/ingest"
    SENTINEL_HOST: str = "localhost"
    SENTINEL_RTSP_PORT: int = 8554
    SENTINEL_WHEP_PORT: int = 8889
    SENTINEL_HLS_PORT: int = 80

    # Evidence Storage
    EVIDENCE_STORAGE_PATH: str = "./data/evidence"

    # Security
    JWT_SECRET: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
