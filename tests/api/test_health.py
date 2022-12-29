"""Tests for the health check endpoints."""
import logging

import pytest
from fastapi.testclient import TestClient

from ralph.api import app
from ralph.api.routers import health
from ralph.backends.database.base import DatabaseStatus

from tests.fixtures.backends import (
    get_clickhouse_test_backend,
    get_es_test_backend,
    get_mongo_test_backend,
)

client = TestClient(app)


@pytest.mark.parametrize(
    "backend",
    [get_clickhouse_test_backend, get_es_test_backend, get_mongo_test_backend],
)
def test_api_health_lbheartbeat(backend, monkeypatch):
    """Test the load balancer heartbeat healthcheck."""
    monkeypatch.setattr(health, "DATABASE_CLIENT", backend())

    response = client.get("/__lbheartbeat__")
    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.parametrize(
    "backend",
    [get_clickhouse_test_backend, get_es_test_backend, get_mongo_test_backend],
)
# pylint: disable=unused-argument
def test_api_health_heartbeat(backend, monkeypatch, clickhouse):
    """Test the heartbeat healthcheck."""
    monkeypatch.setattr(health, "DATABASE_CLIENT", backend())

    response = client.get("/__heartbeat__")
    logging.warning(response.read())
    assert response.status_code == 200
    assert response.json() == {"database": "ok"}

    monkeypatch.setattr(health.DATABASE_CLIENT, "status", lambda: DatabaseStatus.AWAY)
    response = client.get("/__heartbeat__")
    assert response.json() == {"database": "away"}
    assert response.status_code == 500

    monkeypatch.setattr(health.DATABASE_CLIENT, "status", lambda: DatabaseStatus.ERROR)
    response = client.get("/__heartbeat__")
    assert response.json() == {"database": "error"}
    assert response.status_code == 500
