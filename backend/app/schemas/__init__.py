"""Pydantic Schemas Package for SentinelX."""

from app.schemas.camera import (
    CameraBase,
    CameraCreate,
    CameraDetailResponse,
    CameraHealthResponse,
    CameraResponse,
    CameraSourceResponse,
    CameraSyncResult,
    CameraUpdate,
    SentinelIngestCameraItem,
)
from app.schemas.common import (
    APIResponse,
    ErrorDetail,
    PaginatedResponse,
    PaginationMetadata,
    PaginationParams,
    utc_now_iso,
)
from app.schemas.stream import (
    StreamPoolStatus,
    StreamWorkerState,
    StreamWorkerStats,
    VideoFrame,
)
from app.schemas.system import (
    ComponentHealth,
    HealthData,
    SystemStatusData,
    VersionData,
)

__all__ = [
    "APIResponse",
    "PaginatedResponse",
    "PaginationMetadata",
    "PaginationParams",
    "ErrorDetail",
    "utc_now_iso",
    "HealthData",
    "VersionData",
    "ComponentHealth",
    "SystemStatusData",
    "SentinelIngestCameraItem",
    "CameraBase",
    "CameraCreate",
    "CameraUpdate",
    "CameraResponse",
    "CameraDetailResponse",
    "CameraSourceResponse",
    "CameraHealthResponse",
    "CameraSyncResult",
    "VideoFrame",
    "StreamWorkerState",
    "StreamWorkerStats",
    "StreamPoolStatus",
]
