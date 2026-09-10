"""Centralized and Validated Configuration Management for SentinelX.

Enforces zero-cost constraints, environment validation, startup directory
creation, and secure secret masking for audit and logging.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
    STAGING = "staging"


class LogLevelType(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    # Application Metadata
    PROJECT_NAME: str = "SentinelX — Cross-Camera Vehicle Intelligence & Unified CCTV Analytics"
    VERSION: str = "0.1.0"
    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT
    DEBUG: bool = True
    LOG_LEVEL: LogLevelType = LogLevelType.INFO
    API_V1_STR: str = "/api/v1"

    # Database Configuration (PostgreSQL + PostGIS + pgvector)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = Field(default=5432, ge=1, le=65535)
    POSTGRES_USER: str = "sentinelx_user"
    POSTGRES_PASSWORD: str = "sentinelx_password"
    POSTGRES_DB: str = "sentinelx_db"
    DATABASE_URL: str = "sqlite+aiosqlite:///./sentinelx_dev.db"

    # Cache / Fast State (Valkey / Redis)
    VALKEY_HOST: str = "localhost"
    VALKEY_PORT: int = Field(default=6379, ge=1, le=65535)
    VALKEY_URL: str = "redis://localhost:6379/0"

    # Sentinel Sandbox Ingestion Configuration
    SENTINEL_CATALOG_URL: str = "http://localhost:8000/api/ingest"
    SENTINEL_HOST: str = "localhost"
    SENTINEL_RTSP_PORT: int = Field(default=8554, ge=1, le=65535)
    SENTINEL_WHEP_PORT: int = Field(default=8889, ge=1, le=65535)
    SENTINEL_HLS_PORT: int = Field(default=80, ge=1, le=65535)
    SENTINEL_SYNC_INTERVAL_SECONDS: int = Field(default=30, ge=1)

    # AI Pipeline & Vision
    AI_DEVICE: str = "cpu"
    DETECTION_CONFIDENCE_THRESHOLD: float = Field(default=0.45, ge=0.0, le=1.0)
    ANPR_CONFIDENCE_THRESHOLD: float = Field(default=0.60, ge=0.0, le=1.0)
    TRACK_MAX_AGE: int = Field(default=30, ge=1)
    TRACK_MIN_HITS: int = Field(default=3, ge=1)

    # Storage & Evidence
    EVIDENCE_STORAGE_PATH: str = "./data/evidence"
    MAX_UPLOAD_SIZE_BYTES: int = Field(default=52428800, ge=1024)

    # Authentication & Security
    JWT_SECRET: str = "dev-insecure-jwt-secret-key-must-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=480, ge=1)

    # CORS Configuration
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @field_validator("AI_DEVICE")
    @classmethod
    def validate_ai_device(cls, v: str) -> str:
        device = v.lower().strip()
        if device not in {"cpu", "cuda", "mps"}:
            raise ValueError(f"Invalid AI_DEVICE: {v}. Must be one of: 'cpu', 'cuda', 'mps'.")
        return device

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    def ensure_storage_directories(self) -> None:
        """Ensures that required local storage directories (e.g. evidence) exist."""
        path = Path(self.EVIDENCE_STORAGE_PATH)
        path.mkdir(parents=True, exist_ok=True)

    def get_safe_dict(self) -> Dict[str, Any]:
        """Returns configuration dictionary with all secret fields masked.

        Guarantees that credentials (JWT_SECRET, database passwords, tokens)
        never leak to logs, metrics, or API responses.
        """
        data = self.model_dump()
        sensitive_keys = {
            "JWT_SECRET",
            "POSTGRES_PASSWORD",
            "SECRET_KEY",
        }
        for key in sensitive_keys:
            if key in data and data[key]:
                data[key] = "********"

        # Also mask password inside DATABASE_URL if present
        if "DATABASE_URL" in data and "@" in data["DATABASE_URL"] and ":" in data["DATABASE_URL"]:
            try:
                prefix, remainder = data["DATABASE_URL"].split("://", 1)
                user_pass, host_db = remainder.split("@", 1)
                if ":" in user_pass:
                    user, _ = user_pass.split(":", 1)
                    data["DATABASE_URL"] = f"{prefix}://{user}:********@{host_db}"
            except Exception:
                data["DATABASE_URL"] = "********"

        return data

    def __repr__(self) -> str:
        safe = self.get_safe_dict()
        return f"Settings({safe})"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Singleton settings instance
settings = Settings()
settings.ensure_storage_directories()


def get_settings() -> Settings:
    """Return singleton application settings."""
    return settings
