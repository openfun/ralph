"""Tests for the statements endpoint of the Ralph API."""

from importlib import reload

from ralph import conf
from ralph.api.routers import statements
from ralph.backends.lrs.async_es import AsyncESLRSBackend
from ralph.backends.lrs.async_mongo import AsyncMongoLRSBackend
from ralph.backends.lrs.clickhouse import ClickHouseLRSBackend
from ralph.backends.lrs.es import ESLRSBackend
from ralph.backends.lrs.mongo import MongoLRSBackend


def test_api_statements_backend_instance_with_runserver_backend_env(monkeypatch):
    """Tests that given the RALPH_RUNSERVER_BACKEND environment variable, the backend
    instance `BACKEND_CLIENT` should be updated accordingly.
    """
    # Default backend
    assert isinstance(statements.BACKEND_CLIENT, ESLRSBackend)

    # Mongo backend
    monkeypatch.setenv("RALPH_RUNSERVER_BACKEND", "mongo")
    reload(conf)
    assert isinstance(reload(statements).BACKEND_CLIENT, MongoLRSBackend)

    # Elasticsearch backend
    monkeypatch.setenv("RALPH_RUNSERVER_BACKEND", "es")
    reload(conf)
    assert isinstance(reload(statements).BACKEND_CLIENT, ESLRSBackend)

    # ClickHouse backend
    monkeypatch.setenv("RALPH_RUNSERVER_BACKEND", "clickhouse")
    reload(conf)
    assert isinstance(reload(statements).BACKEND_CLIENT, ClickHouseLRSBackend)

    # Async Elasticsearch backend
    monkeypatch.setenv("RALPH_RUNSERVER_BACKEND", "async_es")
    reload(conf)
    assert isinstance(reload(statements).BACKEND_CLIENT, AsyncESLRSBackend)

    # Async Mongo backend
    monkeypatch.setenv("RALPH_RUNSERVER_BACKEND", "async_mongo")
    reload(conf)
    assert isinstance(reload(statements).BACKEND_CLIENT, AsyncMongoLRSBackend)
