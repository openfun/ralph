"""Tests for the health check endpoints."""

import logging

import pytest

from ralph.api.routers import health
from ralph.backends.data.base import DataBackendStatus

from tests.fixtures.backends import (
    get_async_es_test_backend,
    get_async_mongo_test_backend,
    get_clickhouse_test_backend,
    get_es_test_backend,
    get_mongo_test_backend,
)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "backend",
    [
        get_async_es_test_backend,
        get_async_mongo_test_backend,
        get_clickhouse_test_backend,
        get_es_test_backend,
        get_mongo_test_backend,
    ],
)
async def test_api_health_lbheartbeat(client, backend, monkeypatch):
    """Test the load balancer heartbeat healthcheck."""
    monkeypatch.setattr(health, "BACKEND_CLIENT", backend())

    response = await client.get("/__lbheartbeat__")
    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.anyio
@pytest.mark.parametrize(
    "backend",
    [
        get_async_es_test_backend,
        get_async_mongo_test_backend,
        get_clickhouse_test_backend,
        get_es_test_backend,
        get_mongo_test_backend,
    ],
)
async def test_api_health_heartbeat(client, backend, monkeypatch, clickhouse):
    """Test the heartbeat healthcheck."""
    monkeypatch.setattr(health, "BACKEND_CLIENT", backend())

    response = await client.get("/__heartbeat__")
    logging.warning(response.read())
    assert response.status_code == 200
    assert response.json() == {"database": "ok"}

    monkeypatch.setattr(health.BACKEND_CLIENT, "status", lambda: DataBackendStatus.AWAY)
    response = await client.get("/__heartbeat__")
    assert response.json() == {"database": "away"}
    assert response.status_code == 500

    monkeypatch.setattr(
        health.BACKEND_CLIENT, "status", lambda: DataBackendStatus.ERROR
    )
    response = await client.get("/__heartbeat__")
    assert response.json() == {"database": "error"}
    assert response.status_code == 500
