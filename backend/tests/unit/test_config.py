"""Unit tests for configuration validation and safe logging."""

import logging
from pathlib import Path

import pytest
from app.core.config import EnvironmentType, LogLevelType, Settings
from app.core.logging import SafeLogFilter
from pydantic import ValidationError


def test_default_settings_valid():
    """Verify default settings instantiate with expected valid values."""
    s = Settings()
    assert s.PROJECT_NAME.startswith("SentinelX")
    assert s.VERSION == "0.1.0"
    assert s.ENVIRONMENT in list(EnvironmentType)
    assert s.LOG_LEVEL in list(LogLevelType)
    assert 1 <= s.POSTGRES_PORT <= 65535
    assert 1 <= s.SENTINEL_RTSP_PORT <= 65535
    assert 0.0 <= s.DETECTION_CONFIDENCE_THRESHOLD <= 1.0
    assert 0.0 <= s.ANPR_CONFIDENCE_THRESHOLD <= 1.0


def test_invalid_port_raises_validation_error():
    """Verify out-of-range port numbers raise ValidationError."""
    with pytest.raises(ValidationError):
        Settings(POSTGRES_PORT=99999)

    with pytest.raises(ValidationError):
        Settings(SENTINEL_RTSP_PORT=0)


def test_invalid_confidence_threshold():
    """Verify confidence threshold outside [0, 1] raises ValidationError."""
    with pytest.raises(ValidationError):
        Settings(DETECTION_CONFIDENCE_THRESHOLD=1.5)

    with pytest.raises(ValidationError):
        Settings(ANPR_CONFIDENCE_THRESHOLD=-0.1)


def test_invalid_ai_device():
    """Verify unsupported AI_DEVICE raises ValidationError."""
    with pytest.raises(ValidationError):
        Settings(AI_DEVICE="quantum_tpu")


def test_cors_origins_parsing():
    """Verify comma-separated origins are parsed into a list."""
    s = Settings(
        ALLOWED_ORIGINS="http://localhost:3000, http://127.0.0.1:5173 , https://police.gov.in"
    )
    origins = s.cors_origins
    assert len(origins) == 3
    assert "http://localhost:3000" in origins
    assert "http://127.0.0.1:5173" in origins
    assert "https://police.gov.in" in origins


def test_secret_masking_in_safe_dict_and_repr():
    """Verify JWT_SECRET and database passwords never leak in safe dictionaries or representations."""
    raw_secret = "super-secret-production-jwt-key-998877"
    raw_password = "super-secret-postgres-password"
    db_url = "postgresql+asyncpg://admin:super-secret-postgres-password@localhost:5432/sentinelx_db"

    s = Settings(
        JWT_SECRET=raw_secret,
        POSTGRES_PASSWORD=raw_password,
        DATABASE_URL=db_url,
    )

    safe_dict = s.get_safe_dict()
    assert safe_dict["JWT_SECRET"] == "********"
    assert safe_dict["POSTGRES_PASSWORD"] == "********"
    assert raw_secret not in str(safe_dict)
    assert raw_password not in str(safe_dict)

    representation = repr(s)
    assert raw_secret not in representation
    assert raw_password not in representation
    assert "********" in representation


def test_ensure_storage_directories(tmp_path: Path):
    """Verify ensure_storage_directories creates missing evidence storage directories."""
    test_dir = tmp_path / "sentinelx_evidence_test"
    assert not test_dir.exists()

    s = Settings(EVIDENCE_STORAGE_PATH=str(test_dir))
    s.ensure_storage_directories()
    assert test_dir.exists()
    assert test_dir.is_dir()


def test_safe_logging_filter():
    """Verify SafeLogFilter scrubs secrets and passwords from log records."""
    log_filter = SafeLogFilter()
    record = logging.LogRecord(
        name="sentinelx",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg='Connecting with jwt_secret: "secret-token-12345" and password: "my-plain-password"',
        args=(),
        exc_info=None,
    )

    log_filter.filter(record)
    assert "secret-token-12345" not in record.msg
    assert "my-plain-password" not in record.msg
    assert 'jwt_secret: "********"' in record.msg
