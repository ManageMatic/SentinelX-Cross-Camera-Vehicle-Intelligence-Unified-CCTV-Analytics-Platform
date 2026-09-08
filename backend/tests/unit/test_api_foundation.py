"""Unit tests for API Foundation, Middleware, Exception Handlers, and Telemetry."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_request_id_and_duration_headers(async_client: AsyncClient):
    """Test that every request receives an X-Request-ID and X-Process-Time-Ms header."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert "x-process-time-ms" in response.headers

    # Custom passed X-Request-ID should be propagated
    custom_id = "custom-police-cad-trace-9911"
    res_custom = await async_client.get("/health", headers={"X-Request-ID": custom_id})
    assert res_custom.headers["x-request-id"] == custom_id


@pytest.mark.asyncio
async def test_system_status_endpoint(async_client: AsyncClient):
    """Test /api/v1/system/status returns component health and uptime."""
    response = await async_client.get("/api/v1/system/status")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    data = res_data["data"]
    assert data["status"] in ["HEALTHY", "DEGRADED"]
    assert "uptime_seconds" in data
    assert "components" in data
    assert "database" in data["components"]
    assert data["components"]["database"]["status"] == "UP"


@pytest.mark.asyncio
async def test_cors_headers_allowed_origin(async_client: AsyncClient):
    """Test CORS headers returned for configured origin."""
    headers = {"Origin": "http://localhost:5173"}
    response = await async_client.get("/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
