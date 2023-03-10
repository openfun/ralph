"""Tests for the health check endpoints."""

import pytest
from httpx import AsyncClient

from ralph.api import app
from ralph.api.routers import health
from ralph.backends.database.base import DatabaseStatus

from tests.fixtures.backends import (
    get_async_es_test_backend,
    get_clickhouse_test_backend,
    get_es_test_backend,
    get_mongo_test_backend,
)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "backend",
    [
        get_async_es_test_backend,
        get_clickhouse_test_backend,
        get_es_test_backend,
        get_mongo_test_backend,
    ],
)
async def test_api_health_lbheartbeat(backend, monkeypatch):
    """Test the load balancer heartbeat healthcheck."""
    monkeypatch.setattr(health, "DATABASE_CLIENT", backend())

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/__lbheartbeat__")
    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.anyio
@pytest.mark.parametrize(
    "backend",
    [
        get_async_es_test_backend,
        get_clickhouse_test_backend,
        get_es_test_backend,
        get_mongo_test_backend,
    ],
)
# pylint: disable=unused-argument
async def test_api_health_heartbeat(backend, monkeypatch, clickhouse):
    """Test the heartbeat healthcheck."""
    monkeypatch.setattr(health, "DATABASE_CLIENT", backend())

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/__heartbeat__")
    assert response.status_code == 200
    assert response.json() == {"database": "ok"}

    monkeypatch.setattr(health.DATABASE_CLIENT, "status", lambda: DatabaseStatus.AWAY)
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/__heartbeat__")
    assert response.json() == {"database": "away"}
    assert response.status_code == 500

    monkeypatch.setattr(health.DATABASE_CLIENT, "status", lambda: DatabaseStatus.ERROR)
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/__heartbeat__")
    assert response.json() == {"database": "error"}
    assert response.status_code == 500
