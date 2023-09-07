"""Tests for the statements endpoint of the Ralph API."""

from importlib import reload

from ralph import conf
from ralph.api.routers import statements
from ralph.backends.data.clickhouse import ClickHouseDataBackend
from ralph.backends.data.es import ESDataBackend
from ralph.backends.data.mongo import MongoDataBackend


def test_api_statements_backend_instance_with_runserver_backend_env(monkeypatch):
    """Tests that given the RALPH_RUNSERVER_BACKEND environment variable, the backend
    instance `BACKEND_CLIENT` should be updated accordingly.
    """
    # Default backend
    assert isinstance(statements.BACKEND_CLIENT, ESDataBackend)

    # Mongo backend
    monkeypatch.setenv("RALPH_RUNSERVER_BACKEND", "mongo")
    reload(conf)
    assert isinstance(reload(statements).BACKEND_CLIENT, MongoDataBackend)

    # Elasticsearch backend
    monkeypatch.setenv("RALPH_RUNSERVER_BACKEND", "es")
    reload(conf)
    assert isinstance(reload(statements).BACKEND_CLIENT, ESDataBackend)

    # ClickHouse backend
    monkeypatch.setenv("RALPH_RUNSERVER_BACKEND", "clickhouse")
    reload(conf)
    assert isinstance(reload(statements).BACKEND_CLIENT, ClickHouseDataBackend)
