"""Request Logging and Tracing Middleware for SentinelX."""

import time
import uuid
from typing import Callable

from app.core.logging import logger
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Assigns unique X-Request-ID, logs execution latency, and tracks HTTP status."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract or generate unique Request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()
        method = request.method
        path = request.url.path

        try:
            response = await call_next(request)
            process_time_ms = (time.perf_counter() - start_time) * 1000.0

            # Attach request ID and duration to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"

            # Structured logging for API telemetry
            if not path.startswith("/health") and not path.endswith("/openapi.json"):
                logger.info(
                    "[%s] %s %s -> status=%d | duration=%.2fms",
                    request_id,
                    method,
                    path,
                    response.status_code,
                    process_time_ms,
                )

            return response
        except Exception as exc:
            process_time_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(
                "[%s] %s %s FAILED -> %s | duration=%.2fms",
                request_id,
                method,
                path,
                str(exc),
                process_time_ms,
            )
            raise exc
