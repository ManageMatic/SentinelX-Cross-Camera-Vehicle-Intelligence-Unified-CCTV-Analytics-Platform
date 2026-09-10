"""Valkey In-Memory Cache and Stream Broker Schemas for SentinelX."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class CacheGetRequest(BaseModel):
    """Cache query request."""
    key: str = Field(..., description="Target cache key")


class CacheSetRequest(BaseModel):
    """Cache storage request."""
    key: str = Field(..., description="Cache key identifier")
    value: Any = Field(..., description="Arbitrary JSON serializable payload or primitive")
    ttl_seconds: Optional[int] = Field(None, ge=1, description="Optional time-to-live expiration in seconds")


class CacheEntryResponse(BaseModel):
    """Retrieved cache item."""
    key: str
    value: Optional[Any] = None
    ttl_remaining_seconds: Optional[int] = None
    found: bool


class CacheStatsResponse(BaseModel):
    """Live cache broker operational metrics."""
    backend_type: str = Field(..., description="VALKEY_RESP or IN_MEMORY_FALLBACK")
    connected: bool
    total_keys: int
    hits: int
    misses: int
    hit_rate_pct: float
    total_sets: int
    total_deletes: int
    memory_bytes_approx: int


class PubSubPublishRequest(BaseModel):
    """Publish event payload to Valkey pub/sub broker."""
    channel: str = Field(..., description="Topic channel name (e.g. alerts:critical, camera:status)")
    message: Any = Field(..., description="Message payload to broadcast")


class PubSubPublishResponse(BaseModel):
    """Broadcast acknowledgment response."""
    channel: str
    subscribers_count: int
    published_at: datetime


class HotlistCacheSyncResult(BaseModel):
    """Hotlist in-memory synchronization report."""
    total_hotlist_entries: int
    synced_at: datetime
    sync_duration_ms: float
    message: str


class CameraStatusCacheItem(BaseModel):
    """Cached lightweight camera operational status."""
    camera_id: str
    name: str
    live_status: bool
    fps: float
    last_ping: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
