"""Valkey In-Memory Cache and Stream Broker REST API Endpoints for SentinelX."""

from datetime import datetime, timezone

from app.db.session import get_db
from app.schemas.cache import (
    CacheEntryResponse,
    CacheSetRequest,
    CacheStatsResponse,
    HotlistCacheSyncResult,
    PubSubPublishRequest,
    PubSubPublishResponse,
)
from app.schemas.common import APIResponse
from app.services.valkey_broker import valkey_broker
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/cache", tags=["Valkey In-Memory Cache & Broker"])


@router.get(
    "/get",
    response_model=APIResponse[CacheEntryResponse],
    summary="Retrieve value from memory cache by key",
)
async def get_cache_key(
    key: str = Query(..., description="Cache key identifier"),
) -> APIResponse[CacheEntryResponse]:
    """Retrieve fast cached item in sub-millisecond time."""
    val = await valkey_broker.get(key)
    found = val is not None
    return APIResponse(
        data=CacheEntryResponse(key=key, value=val, found=found),
        message=f"Cache key '{key}' {'found' if found else 'miss'}.",
    )


@router.post(
    "/set",
    response_model=APIResponse[dict],
    summary="Store value in cache with optional TTL",
)
async def set_cache_key(
    payload: CacheSetRequest,
) -> APIResponse[dict]:
    """Set cache key-value pair."""
    success = await valkey_broker.set(payload.key, payload.value, ttl_seconds=payload.ttl_seconds)
    return APIResponse(
        data={"key": payload.key, "stored": success, "ttl_seconds": payload.ttl_seconds},
        message=f"Key '{payload.key}' stored successfully.",
    )


@router.delete(
    "/delete",
    response_model=APIResponse[dict],
    summary="Remove key from cache",
)
async def delete_cache_key(
    key: str = Query(..., description="Key to delete"),
) -> APIResponse[dict]:
    """Delete key from cache."""
    deleted = await valkey_broker.delete(key)
    return APIResponse(
        data={"key": key, "deleted": deleted},
        message=f"Key '{key}' deleted." if deleted else f"Key '{key}' not found.",
    )


@router.post(
    "/flush",
    response_model=APIResponse[dict],
    summary="Flush all keys in cache namespace",
)
async def flush_cache() -> APIResponse[dict]:
    """Clear entire cache."""
    await valkey_broker.flush()
    return APIResponse(data={"flushed": True}, message="Cache namespace flushed.")


@router.get(
    "/stats",
    response_model=APIResponse[CacheStatsResponse],
    summary="Get live cache performance and operational metrics",
)
async def get_cache_stats() -> APIResponse[CacheStatsResponse]:
    """Retrieve hit rates, active key counts, and memory usage."""
    stats = await valkey_broker.get_stats()
    return APIResponse(data=stats, message="Cache operational stats retrieved.")


@router.post(
    "/publish",
    response_model=APIResponse[PubSubPublishResponse],
    summary="Publish event to Valkey pub/sub broker channel",
)
async def publish_event(
    payload: PubSubPublishRequest,
) -> APIResponse[PubSubPublishResponse]:
    """Broadcast an event payload to all topic subscribers."""
    sub_count = await valkey_broker.publish(payload.channel, payload.message)
    resp = PubSubPublishResponse(
        channel=payload.channel,
        subscribers_count=sub_count,
        published_at=datetime.now(timezone.utc),
    )
    return APIResponse(data=resp, message=f"Broadcasted to {sub_count} subscribers on channel '{payload.channel}'.")


@router.post(
    "/sync-hotlist",
    response_model=APIResponse[HotlistCacheSyncResult],
    summary="Sync database police hotlist records into fast memory cache",
)
async def sync_hotlist(
    db: AsyncSession = Depends(get_db),
) -> APIResponse[HotlistCacheSyncResult]:
    """Synchronize active watchlist entries into memory index."""
    result = await valkey_broker.sync_hotlist_to_memory(db)
    return APIResponse(data=result, message=result.message)


@router.get(
    "/camera-status/{camera_id}",
    response_model=APIResponse[dict],
    summary="Fast sub-millisecond camera live state check",
)
async def get_camera_status(
    camera_id: str,
) -> APIResponse[dict]:
    """Check fast cached camera heartbeat without DB query overhead."""
    status_data = await valkey_broker.get_camera_status(camera_id)
    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera status not cached for camera '{camera_id}'.",
        )

    return APIResponse(data=status_data, message=f"Camera status retrieved for '{camera_id}'.")
