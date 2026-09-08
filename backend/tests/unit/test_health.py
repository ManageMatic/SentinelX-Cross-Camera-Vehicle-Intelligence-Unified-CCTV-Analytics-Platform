"""Unit tests for health and version endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_health_endpoint(async_client: AsyncClient):
    """Test root /health endpoint returns 200 and healthy status."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "service" in data


@pytest.mark.asyncio
async def test_api_v1_health_endpoint(async_client: AsyncClient):
    """Test /api/v1/health endpoint."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_api_version_endpoint(async_client: AsyncClient):
    """Test /api/version and /api/v1/version endpoints."""
    response = await async_client.get("/api/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "project" in data

    response_v1 = await async_client.get("/api/v1/version")
    assert response_v1.status_code == 200
    data_v1 = response_v1.json()
    assert data_v1["api_version"] == "v1"


@pytest.mark.asyncio
async def test_404_not_found(async_client: AsyncClient):
    """Test non-existent route returns 404."""
    response = await async_client.get("/non-existent-path")
    assert response.status_code == 404
