"""Custom Application Exceptions and Centralized Handlers for SentinelX."""

from typing import List, Optional

from app.core.config import settings
from app.core.logging import logger
from app.schemas.common import APIResponse, ErrorDetail
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException


class SentinelXException(Exception):
    """Base application exception for SentinelX domain errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        code: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code or "APPLICATION_ERROR"


class ResourceNotFoundException(SentinelXException):
    """Raised when a requested resource (Camera, Vehicle, Alert, Evidence) is not found."""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
        )


class ValidationException(SentinelXException):
    """Raised when domain validation fails."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Registers centralized exception handlers mapping domain & framework exceptions to standard APIResponse envelopes."""

    @app.exception_handler(SentinelXException)
    async def handle_sentinelx_exception(request: Request, exc: SentinelXException):
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=APIResponse(
                success=False,
                message=exc.message,
                errors=[ErrorDetail(message=exc.message, code=exc.code)],
                request_id=request_id,
            ).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        request_id = getattr(request.state, "request_id", None)
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error occurred"
        return JSONResponse(
            status_code=exc.status_code,
            content=APIResponse(
                success=False,
                message=message,
                errors=[ErrorDetail(message=message, code=f"HTTP_{exc.status_code}")],
                request_id=request_id,
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", None)
        errors: List[ErrorDetail] = []
        for err in exc.errors():
            loc = " -> ".join([str(x) for x in err.get("loc", []) if x != "body"])
            msg = err.get("msg", "Invalid parameter")
            errors.append(ErrorDetail(field=loc or None, message=msg, code="INVALID_INPUT"))

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=APIResponse(
                success=False,
                message="Request validation failed. Please check input parameters.",
                errors=errors,
                request_id=request_id,
            ).model_dump(),
        )

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(request: Request, exc: IntegrityError):
        request_id = getattr(request.state, "request_id", None)
        logger.warning("[%s] Database integrity constraint violation: %s", request_id, str(exc))
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=APIResponse(
                success=False,
                message="Database constraint violation (e.g. duplicate key or conflict).",
                errors=[
                    ErrorDetail(
                        message="Duplicate entity or invalid reference.", code="DB_INTEGRITY_ERROR"
                    )
                ],
                request_id=request_id,
            ).model_dump(),
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_sqlalchemy_error(request: Request, exc: SQLAlchemyError):
        request_id = getattr(request.state, "request_id", None)
        logger.error(
            "[%s] Database query execution failure: %s",
            request_id,
            str(exc),
            exc_info=settings.DEBUG,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIResponse(
                success=False,
                message="A database error occurred while processing the request.",
                errors=[ErrorDetail(message="Internal database error.", code="DB_ERROR")],
                request_id=request_id,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_generic_exception(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        logger.error(
            "[%s] Unhandled exception on %s %s: %s",
            request_id,
            request.method,
            request.url.path,
            str(exc),
            exc_info=settings.DEBUG,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIResponse(
                success=False,
                message="An unexpected internal server error occurred. Please contact the administrator.",
                errors=[
                    ErrorDetail(message="Internal server error.", code="INTERNAL_SERVER_ERROR")
                ],
                request_id=request_id,
            ).model_dump(),
        )
