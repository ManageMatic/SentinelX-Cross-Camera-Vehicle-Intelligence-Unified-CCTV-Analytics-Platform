"""Standardized Pydantic v2 Common Schemas & Response Envelopes for SentinelX."""

from datetime import datetime, timezone
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


def utc_now_iso() -> str:
    """Returns current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


class ErrorDetail(BaseModel):
    """Structured error message details."""

    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class APIResponse(BaseModel, Generic[T]):
    """Standardized API Response Envelope for all SentinelX endpoints."""

    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None
    errors: Optional[List[ErrorDetail]] = None
    timestamp: str = Field(default_factory=utc_now_iso)
    request_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    """Standardized Query Pagination Parameters."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")
    sort_by: Optional[str] = Field(default="created_at", description="Field to sort by")
    sort_order: Optional[str] = Field(
        default="desc", pattern="^(asc|desc)$", description="Sort direction"
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginationMetadata(BaseModel):
    """Pagination metadata container."""

    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized Paginated Response Envelope."""

    success: bool = True
    message: str = "Data retrieved successfully"
    data: List[T] = Field(default_factory=list)
    pagination: PaginationMetadata
    timestamp: str = Field(default_factory=utc_now_iso)
    request_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
