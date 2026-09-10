"""Comprehensive Unit Tests for Dynamic Camera Catalog Ingestion Engine (Module 5)."""

import pytest
from app.main import app
from app.models.camera import Camera
from app.services.camera_catalog import CameraCatalogService
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_normalize_camera_item():
    """Verify normalization of irregular and heterogeneous camera payloads from Sentinel /api/ingest."""
    service = CameraCatalogService()

    # Case 1: Standard payload
    raw_1 = {
        "camera_id": "GJ-AHM-001",
        "name": "SG Highway North",
        "location": "Ahmedabad SG Highway",
        "latitude": 23.0338,
        "longitude": 72.5072,
        "rtsp_url": "rtsp://10.0.0.1:554/live/stream1",
        "fps": 30.0,
        "status": "ONLINE",
    }
    norm_1 = service.normalize_camera_item(raw_1, index=0)
    assert norm_1.external_camera_id == "GJ-AHM-001"
    assert norm_1.name == "SG Highway North"
    assert norm_1.latitude == 23.0338
    assert norm_1.longitude == 72.5072
    assert norm_1.rtsp_url == "rtsp://10.0.0.1:554/live/stream1"
    assert norm_1.fps == 30.0
    assert norm_1.live_status is True

    # Case 2: Minimal payload with aliases (id, lat, lng, stream_url)
    raw_2 = {
        "id": "104",
        "lat": 23.2156,
        "lng": 72.6369,
        "stream_url": "rtsp://10.0.0.2:8554/cam104",
    }
    norm_2 = service.normalize_camera_item(raw_2, index=1)
    assert norm_2.external_camera_id == "104"
    assert norm_2.latitude == 23.2156
    assert norm_2.longitude == 72.6369
    assert norm_2.rtsp_url == "rtsp://10.0.0.2:8554/cam104"


@pytest.mark.asyncio
async def test_sync_catalog_to_db_idempotent(db_session: AsyncSession):
    """Test idempotent synchronization of camera feeds into database."""
    service = CameraCatalogService()

    catalog_data = [
        {
            "camera_id": "TEST-CAM-01",
            "name": "Test Junction 1",
            "location_name": "Gandhinagar Sector 1",
            "latitude": 23.2200,
            "longitude": 72.6400,
            "rtsp_url": "rtsp://127.0.0.1:8554/test_cam_01",
            "fps": 25.0,
            "status": "ONLINE",
        },
        {
            "camera_id": "TEST-CAM-02",
            "name": "Test Junction 2",
            "location_name": "Gandhinagar Sector 2",
            "latitude": 23.2300,
            "longitude": 72.6500,
            "rtsp_url": "rtsp://127.0.0.1:8554/test_cam_02",
            "fps": 25.0,
            "status": "ONLINE",
        },
    ]

    # Initial sync (Both should be added)
    result_1 = await service.sync_catalog_to_db(
        db=db_session, catalog_url="http://mock/api/ingest", raw_items=catalog_data
    )
    assert result_1.total_discovered == 2
    assert result_1.added_count == 2
    assert result_1.updated_count == 0
    assert result_1.unchanged_count == 0
    assert result_1.errors_count == 0

    # Verify database records
    stmt = select(Camera).where(Camera.external_camera_id.in_(["TEST-CAM-01", "TEST-CAM-02"]))
    cams = (await db_session.execute(stmt)).scalars().all()
    assert len(cams) == 2

    # Second sync with NO changes (Both should be unchanged)
    result_2 = await service.sync_catalog_to_db(
        db=db_session, catalog_url="http://mock/api/ingest", raw_items=catalog_data
    )
    assert result_2.added_count == 0
    assert result_2.updated_count == 0
    assert result_2.unchanged_count == 2

    # Third sync with 1 updated URL and 1 new camera
    catalog_data_updated = [
        {
            "camera_id": "TEST-CAM-01",
            "name": "Test Junction 1 Updated",
            "location_name": "Gandhinagar Sector 1",
            "latitude": 23.2200,
            "longitude": 72.6400,
            "rtsp_url": "rtsp://127.0.0.1:8554/test_cam_01_new_port",
            "fps": 30.0,
            "status": "ONLINE",
        },
        catalog_data[1],  # Unchanged
        {
            "camera_id": "TEST-CAM-03",
            "name": "Test Junction 3 New",
            "location_name": "Gandhinagar Sector 3",
            "latitude": 23.2400,
            "longitude": 72.6600,
            "rtsp_url": "rtsp://127.0.0.1:8554/test_cam_03",
            "fps": 25.0,
            "status": "ONLINE",
        },
    ]

    result_3 = await service.sync_catalog_to_db(
        db=db_session, catalog_url="http://mock/api/ingest", raw_items=catalog_data_updated
    )
    assert result_3.total_discovered == 3
    assert result_3.added_count == 1
    assert result_3.updated_count == 1
    assert result_3.unchanged_count == 1


@pytest.mark.asyncio
async def test_camera_api_endpoints(db_session: AsyncSession):
    """Test camera REST API endpoints for listing, filtering, and manual creation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register a new camera via POST /api/v1/cameras
        create_payload = {
            "external_camera_id": "API-TEST-CAM-01",
            "name": "API Test Camera",
            "location_name": "Ahmedabad Ring Road",
            "department": "Traffic Police",
            "latitude": 23.0500,
            "longitude": 72.5200,
            "vendor": "Generic RTSP",
            "vms": "Sentinel VMS",
            "protocol": "RTSP/TCP",
            "codec": "H264",
            "width": 1920,
            "height": 1080,
            "fps": 25.0,
            "rtsp_url": "rtsp://127.0.0.1:8554/api_test_01",
            "whep_url": "http://127.0.0.1:8889/api_test_01/whep",
            "live_status": True,
            "is_active_for_ai": True,
        }

        resp_create = await client.post("/api/v1/cameras", json=create_payload)
        assert resp_create.status_code == 201
        data_create = resp_create.json()
        assert data_create["success"] is True
        assert data_create["data"]["external_camera_id"] == "API-TEST-CAM-01"

        # 2. List cameras via GET /api/v1/cameras
        resp_list = await client.get("/api/v1/cameras?search=API-TEST-CAM-01")
        assert resp_list.status_code == 200
        data_list = resp_list.json()
        assert data_list["pagination"]["total_items"] >= 1
        assert len(data_list["data"]) >= 1

        # 3. Get camera details via GET /api/v1/cameras/{id}
        resp_detail = await client.get("/api/v1/cameras/API-TEST-CAM-01")
        assert resp_detail.status_code == 200
        data_detail = resp_detail.json()
        assert data_detail["success"] is True
        assert data_detail["data"]["external_camera_id"] == "API-TEST-CAM-01"
        assert len(data_detail["data"]["sources"]) >= 1

        # 4. Update camera via PATCH /api/v1/cameras/{id}
        resp_patch = await client.patch(
            "/api/v1/cameras/API-TEST-CAM-01",
            json={"name": "API Test Camera Renamed", "fps": 30.0},
        )
        assert resp_patch.status_code == 200
        data_patch = resp_patch.json()
        assert data_patch["data"]["name"] == "API Test Camera Renamed"
        assert data_patch["data"]["fps"] == 30.0
