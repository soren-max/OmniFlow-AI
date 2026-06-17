"""Tests for the health check endpoint.

Uses httpx AsyncClient as required by AGENTS.md Testing Rules.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from api.app.main import app  # type: ignore[import-untyped]
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client using httpx ASGITransport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check_returns_ok(client: AsyncClient) -> None:
    """Test that /health returns 200 with status ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "contentops-api"


@pytest.mark.asyncio
async def test_health_check_rejects_post(client: AsyncClient) -> None:
    """Test that /health rejects non-GET methods."""
    response = await client.post("/health")
    assert response.status_code == 405  # Method Not Allowed


@pytest.mark.asyncio
async def test_root_returns_service_info(client: AsyncClient) -> None:
    """Test that the root endpoint returns service metadata."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "docs" in data
    assert "health" in data


@pytest.mark.asyncio
async def test_missing_route_returns_error_envelope(client: AsyncClient) -> None:
    """Test that HTTP errors use the standard API response envelope."""
    response = await client.get("/missing")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["data"] is None
    assert data["error"]["code"] == "HTTP_ERROR"
    assert data["error"]["message"] == "Not Found"
