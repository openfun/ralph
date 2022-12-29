"""Tests for the statements endpoint of the Ralph API."""

from importlib import reload

from ralph import conf
from ralph.api.routers import statements
from ralph.backends.database.clickhouse import ClickHouseDatabase
from ralph.backends.database.es import ESDatabase
from ralph.backends.database.mongo import MongoDatabase


def test_api_statements_backend_instance_with_runserver_backend_env(monkeypatch):
    """Tests that given the RALPH_RUNSERVER_BACKEND environment variable, the backend
    instance `DATABASE_CLIENT` should be updated accordingly.
    """
    # Default backend
    assert isinstance(statements.DATABASE_CLIENT, ESDatabase)

    # Mongo backend
    monkeypatch.setenv("RALPH_RUNSERVER_BACKEND", "mongo")
    reload(conf)
    assert isinstance(reload(statements).DATABASE_CLIENT, MongoDatabase)

    # Elastisearch backend
    monkeypatch.setenv("RALPH_RUNSERVER_BACKEND", "es")
    reload(conf)
    assert isinstance(reload(statements).DATABASE_CLIENT, ESDatabase)

    # ClickHouse backend
    monkeypatch.setenv("RALPH_RUNSERVER_BACKEND", "clickhouse")
    reload(conf)
    assert isinstance(reload(statements).DATABASE_CLIENT, ClickHouseDatabase)
