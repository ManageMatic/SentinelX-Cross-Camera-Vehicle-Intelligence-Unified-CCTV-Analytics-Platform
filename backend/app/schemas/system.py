"""Health, Version, and System Status Schemas for SentinelX."""

from typing import Dict, Optional

from pydantic import BaseModel, Field


class HealthData(BaseModel):
    """Payload for health status response."""

    status: str = "healthy"
    service: str
    version: str
    environment: str
    database_connected: bool = True
    storage_accessible: bool = True


class VersionData(BaseModel):
    """Payload for version response."""

    project: str
    version: str
    api_version: str = "v1"
    license: str = "100% Free & Open-Source (Apache-2.0 / MIT)"


class ComponentHealth(BaseModel):
    """Individual component health status."""

    status: str = "UP"  # UP, DOWN, DEGRADED
    latency_ms: Optional[float] = None
    details: Optional[str] = None


class SystemStatusData(BaseModel):
    """Comprehensive system status and telemetry payload."""

    status: str = "HEALTHY"
    version: str
    environment: str
    uptime_seconds: float
    components: Dict[str, ComponentHealth] = Field(default_factory=dict)
