"""Comprehensive Unit Tests for Valkey In-Memory Cache & Stream Broker (Module 23)."""

import asyncio
import uuid

import pytest
from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.watchlist import Watchlist, WatchlistCategory, WatchlistEntry
from app.services.valkey_broker import valkey_broker
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_cache_kv_crud_and_ttl():
    """Test basic key-value operations, TTL expiration, and deletion."""
    key = f"test:key:{uuid.uuid4().hex[:6]}"
    val = {"status": "ACTIVE", "count": 42}

    # 1. Set and Get
    assert await valkey_broker.set(key, val) is True
    retrieved = await valkey_broker.get(key)
    assert retrieved == val
    assert await valkey_broker.exists(key) is True

    # 2. TTL Expiration
    ttl_key = f"test:ttl:{uuid.uuid4().hex[:6]}"
    await valkey_broker.set(ttl_key, "expiring_val", ttl_seconds=1)
    assert await valkey_broker.get(ttl_key) == "expiring_val"
    await asyncio.sleep(1.05)
    assert await valkey_broker.get(ttl_key) is None

    # 3. Delete
    assert await valkey_broker.delete(key) is True
    assert await valkey_broker.get(key) is None


@pytest.mark.asyncio
async def test_batch_operations_and_wildcards():
    """Test batch mset/mget and glob pattern key scanning."""
    prefix = f"cam:{uuid.uuid4().hex[:4]}"
    batch = {
        f"{prefix}:01": {"fps": 30.0},
        f"{prefix}:02": {"fps": 25.0},
        f"{prefix}:03": {"fps": 60.0},
        f"other:{prefix}": {"ignored": True},
    }

    # 1. Batch Set
    assert await valkey_broker.mset(batch) is True

    # 2. Batch Get
    subset = [f"{prefix}:01", f"{prefix}:02"]
    mget_res = await valkey_broker.mget(subset)
    assert len(mget_res) == 2
    assert mget_res[f"{prefix}:01"]["fps"] == 30.0

    # 3. Wildcard Pattern Matching
    matched_keys = await valkey_broker.keys(f"{prefix}:*")
    assert len(matched_keys) == 3
    assert f"other:{prefix}" not in matched_keys


@pytest.mark.asyncio
async def test_pubsub_messaging_flow():
    """Test publish/subscribe message delivery across topic channels."""
    channel = f"channel:alerts:{uuid.uuid4().hex[:6]}"
    sub_id, queue = await valkey_broker.subscribe(channel)

    test_payload = {"alert_id": "ALT-1234", "plate": "GJ01XY9999", "priority": "CRITICAL"}

    # Publish message
    sub_count = await valkey_broker.publish(channel, test_payload)
    assert sub_count == 1

    # Receive message from queue
    received = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert received == test_payload

    # Unsubscribe
    await valkey_broker.unsubscribe(channel, sub_id)
    sub_count_after = await valkey_broker.publish(channel, {"empty": True})
    assert sub_count_after == 0


@pytest.mark.asyncio
async def test_camera_status_and_hotlist_sync():
    """Test high-frequency camera status caching and DB hotlist memory indexing."""
    cam_id = f"CAM-TEST-{uuid.uuid4().hex[:6]}"
    status_data = {"name": "Test Junction Cam", "live_status": True, "fps": 28.5}

    # 1. Camera Status
    await valkey_broker.cache_camera_status(cam_id, status_data)
    cached_cam = await valkey_broker.get_camera_status(cam_id)
    assert cached_cam is not None
    assert cached_cam["fps"] == 28.5
    assert cached_cam["live_status"] is True

    # 2. Hotlist Sync
    async with AsyncSessionLocal() as session:
        wl_id = str(uuid.uuid4())
        wl_name = f"Valkey Sync Test Hotlist {uuid.uuid4().hex[:6]}"
        wl = Watchlist(
            id=wl_id,
            name=wl_name,
            category=WatchlistCategory.STOLEN.value,
        )
        session.add(wl)
        await session.flush()

        test_plate = f"GJ01VK{uuid.uuid4().hex[:4].upper()}"
        entry = WatchlistEntry(
            id=str(uuid.uuid4()),
            watchlist_id=wl_id,
            registration_number=test_plate,
            registration_normalized=test_plate,
            notes="Valkey test vehicle",
            is_active=True,
        )
        session.add(entry)
        await session.commit()

        # Sync to memory cache
        sync_res = await valkey_broker.sync_hotlist_to_memory(session)
        assert sync_res.total_hotlist_entries >= 1

        # Direct cache lookup
        cached_entry = await valkey_broker.get(f"hotlist:plate:{test_plate}")
        assert cached_entry is not None
        assert cached_entry["plate_number"] == test_plate

        assert cached_entry["category"] == "STOLEN"


@pytest.mark.asyncio
async def test_cache_stats_and_hit_rate():
    """Test cache metrics, hits/misses counters, and memory estimation."""
    stat_key = f"stat:key:{uuid.uuid4().hex[:6]}"
    await valkey_broker.set(stat_key, "value_stat")

    # Generate hit
    await valkey_broker.get(stat_key)
    # Generate miss
    await valkey_broker.get("nonexistent_miss_key_123")

    stats = await valkey_broker.get_stats()
    assert stats.connected is True
    assert stats.hits >= 1
    assert stats.misses >= 1
    assert 0.0 <= stats.hit_rate_pct <= 100.0


@pytest.mark.asyncio
async def test_cache_rest_api_endpoints():
    """Test full REST API integration for Valkey Cache & Broker endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        test_key = f"api:key:{uuid.uuid4().hex[:6]}"

        # 1. Set key via API
        set_resp = await client.post(
            "/api/v1/cache/set",
            json={"key": test_key, "value": {"test": "data", "num": 100}, "ttl_seconds": 3600},
        )
        assert set_resp.status_code == 200
        assert set_resp.json()["data"]["stored"] is True

        # 2. Get key via API
        get_resp = await client.get(f"/api/v1/cache/get?key={test_key}")
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["found"] is True
        assert get_resp.json()["data"]["value"]["num"] == 100

        # 3. Stats Endpoint
        stats_resp = await client.get("/api/v1/cache/stats")
        assert stats_resp.status_code == 200
        assert "hit_rate_pct" in stats_resp.json()["data"]

        # 4. Pub/Sub Publish Endpoint
        pub_resp = await client.post(
            "/api/v1/cache/publish",
            json={"channel": "system:notifications", "message": {"text": "Broadcast Alert"}},
        )
        assert pub_resp.status_code == 200
        assert "published_at" in pub_resp.json()["data"]

        # 5. Sync Hotlist Endpoint
        sync_resp = await client.post("/api/v1/cache/sync-hotlist")
        assert sync_resp.status_code == 200
        assert sync_resp.json()["data"]["total_hotlist_entries"] >= 0

        # 6. Delete key via API
        del_resp = await client.delete(f"/api/v1/cache/delete?key={test_key}")
        assert del_resp.status_code == 200
        assert del_resp.json()["data"]["deleted"] is True
