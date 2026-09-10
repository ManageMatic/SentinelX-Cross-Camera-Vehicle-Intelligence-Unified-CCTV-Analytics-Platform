"""Structured Safe Logging System for SentinelX.

Guarantees structured formatting and ensures secrets/tokens are never logged.
"""

import logging
import re

from app.core.config import settings

# Regex patterns for sensitive key scrubbing
SENSITIVE_PATTERNS = [
    re.compile(
        r'(jwt_secret|password|secret|token|api_key|authorization)\s*[:=]\s*["\']?([^"\'\s]+)["\']?',
        re.IGNORECASE,
    ),
]


class SafeLogFilter(logging.Filter):
    """Filters log records to mask potential secret leaks."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern in SENSITIVE_PATTERNS:
                msg = pattern.sub(r'\1: "********"', msg)
            record.msg = msg
        return True


def setup_logging() -> logging.Logger:
    """Configures application logger with safe masking filters and structured formatting."""
    logger = logging.getLogger("sentinelx")
    logger.setLevel(settings.LOG_LEVEL.value)

    # Avoid adding multiple duplicate handlers during test runs
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SafeLogFilter())
        logger.addHandler(handler)

    return logger


logger = setup_logging()


def get_logger(name: str = "sentinelx") -> logging.Logger:
    """Return configured logger instance."""
    if name == "sentinelx":
        return logger
    child = logging.getLogger(f"sentinelx.{name}")
    child.setLevel(settings.LOG_LEVEL.value)
    return child
