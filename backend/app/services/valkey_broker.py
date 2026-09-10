"""Valkey In-Memory Cache and Stream Broker Service for SentinelX.

Provides sub-millisecond key-value caching, TTL eviction, wildcard key scanning,
camera live state buffering, police hotlist in-memory hash indexing, and asynchronous
pub/sub message distribution with zero-dependency in-memory fallback.
"""

from __future__ import annotations

import asyncio
import fnmatch
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.models.watchlist import WatchlistEntry
from app.schemas.cache import (
    CacheStatsResponse,
    HotlistCacheSyncResult,
)


class ValkeyCacheBroker:
    """High-Performance Valkey Cache & Stream Broker."""

    def __init__(self) -> None:
        # In-memory storage: key -> (value, expiry_timestamp_float_or_None)
        self._store: Dict[str, Tuple[Any, Optional[float]]] = {}
        # Pub/Sub queues: channel -> {sub_id: asyncio.Queue}
        self._pubsub: Dict[str, Dict[str, asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

        # Telemetry metrics
        self._hits: int = 0
        self._misses: int = 0
        self._total_sets: int = 0
        self._total_deletes: int = 0
        self._backend_type: str = "IN_MEMORY_FALLBACK"

    def _is_expired(self, expiry: Optional[float]) -> bool:
        """Check if an expiration timestamp has elapsed."""
        if expiry is None:
            return False
        return time.time() > expiry

    def _purge_expired(self) -> None:
        """Prune expired keys on demand."""
        now = time.time()
        expired_keys = [k for k, (_, exp) in self._store.items() if exp is not None and now > exp]
        for k in expired_keys:
            del self._store[k]

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache with TTL check."""
        async with self._lock:
            if key not in self._store:
                self._misses += 1
                return None

            val, expiry = self._store[key]
            if self._is_expired(expiry):
                del self._store[key]
                self._misses += 1
                return None

            self._hits += 1
            return val

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Store key-value pair with optional TTL."""
        expiry = (time.time() + ttl_seconds) if (ttl_seconds and ttl_seconds > 0) else None
        async with self._lock:
            self._store[key] = (value, expiry)
            self._total_sets += 1
        return True

    async def delete(self, key: str) -> bool:
        """Remove key from cache."""
        async with self._lock:
            if key in self._store:
                del self._store[key]
                self._total_deletes += 1
                return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if key exists and is unexpired."""
        val = await self.get(key)
        return val is not None

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Batch retrieve multiple keys."""
        results: Dict[str, Any] = {}
        for k in keys:
            val = await self.get(k)
            if val is not None:
                results[k] = val
        return results

    async def mset(self, items: Dict[str, Any], ttl_seconds: Optional[int] = None) -> bool:
        """Batch set multiple key-value pairs."""
        for k, v in items.items():
            await self.set(k, v, ttl_seconds=ttl_seconds)
        return True

    async def keys(self, pattern: str = "*") -> List[str]:
        """Scan active unexpired keys matching glob pattern."""
        async with self._lock:
            self._purge_expired()
            all_keys = list(self._store.keys())

        if pattern == "*":
            return all_keys
        return [k for k in all_keys if fnmatch.fnmatch(k, pattern)]

    async def flush(self) -> bool:
        """Clear entire cache namespace."""
        async with self._lock:
            self._store.clear()
        return True

    # --- Pub/Sub Messaging ---

    async def publish(self, channel: str, message: Any) -> int:
        """Publish message to all subscribers of a channel."""
        subscribers = self._pubsub.get(channel, {})
        dead_subs: Set[str] = set()

        count = 0
        for sub_id, queue in list(subscribers.items()):
            try:
                queue.put_nowait(message)
                count += 1
            except asyncio.QueueFull:
                dead_subs.add(sub_id)

        for sub_id in dead_subs:
            subscribers.pop(sub_id, None)

        return count

    async def subscribe(self, channel: str) -> Tuple[str, asyncio.Queue]:
        """Subscribe to a topic channel and receive dedicated message queue."""
        sub_id = str(uuid.uuid4())
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            if channel not in self._pubsub:
                self._pubsub[channel] = {}
            self._pubsub[channel][sub_id] = queue
        return sub_id, queue

    async def unsubscribe(self, channel: str, sub_id: str) -> None:
        """Remove channel subscription queue."""
        async with self._lock:
            if channel in self._pubsub:
                self._pubsub[channel].pop(sub_id, None)
                if not self._pubsub[channel]:
                    del self._pubsub[channel]

    # --- Domain-Specific Caching ---

    async def cache_camera_status(self, camera_id: str, status_data: Dict[str, Any], ttl: int = 60) -> bool:
        """Cache high-frequency camera live streaming state."""
        key = f"camera:status:{camera_id}"
        payload = {
            **status_data,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }
        return await self.set(key, payload, ttl_seconds=ttl)

    async def get_camera_status(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached camera live streaming state in sub-millisecond time."""
        key = f"camera:status:{camera_id}"
        return await self.get(key)

    async def sync_hotlist_to_memory(self, db: AsyncSession) -> HotlistCacheSyncResult:
        """Synchronize active database hotlist entries into high-speed memory cache."""
        t_start = time.perf_counter()
        query = select(WatchlistEntry).options(selectinload(WatchlistEntry.watchlist)).where(
            WatchlistEntry.is_active == True  # noqa: E712
        )
        res = await db.execute(query)
        entries = res.scalars().all()

        hotlist_map: Dict[str, Any] = {}
        for entry in entries:
            plate = entry.registration_normalized or entry.registration_number
            key = f"hotlist:plate:{plate}"
            cat_val = entry.watchlist.category if entry.watchlist else "GENERAL"
            hotlist_map[key] = {
                "entry_id": entry.id,
                "plate_number": plate,
                "watchlist_id": entry.watchlist_id,
                "watchlist_name": entry.watchlist.name if entry.watchlist else "General",
                "category": cat_val,
                "notes": entry.notes,
            }

        await self.mset(hotlist_map, ttl_seconds=86400)
        elapsed_ms = (time.perf_counter() - t_start) * 1000


        logger.info(f"Synchronized {len(entries)} hotlist plates into memory cache ({elapsed_ms:.2f}ms).")
        return HotlistCacheSyncResult(
            total_hotlist_entries=len(entries),
            synced_at=datetime.now(timezone.utc),
            sync_duration_ms=round(elapsed_ms, 2),
            message=f"Synced {len(entries)} hotlist records into memory index.",
        )

    async def get_stats(self) -> CacheStatsResponse:
        """Compute operational cache metrics and hit rate."""
        async with self._lock:
            self._purge_expired()
            total_keys = len(self._store)

        total_ops = self._hits + self._misses
        hit_rate = (self._hits / total_ops * 100.0) if total_ops > 0 else 0.0

        # Estimate memory footprint
        approx_bytes = sum(sys.getsizeof(k) + sys.getsizeof(v) for k, (v, _) in self._store.items())

        return CacheStatsResponse(
            backend_type=self._backend_type,
            connected=True,
            total_keys=total_keys,
            hits=self._hits,
            misses=self._misses,
            hit_rate_pct=round(hit_rate, 2),
            total_sets=self._total_sets,
            total_deletes=self._total_deletes,
            memory_bytes_approx=approx_bytes,
        )


# Global singleton instance
valkey_broker = ValkeyCacheBroker()
