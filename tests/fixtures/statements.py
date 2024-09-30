"""Test fixtures for statements."""

import pytest
from elasticsearch.helpers import bulk

from ralph.backends.data.base import BaseOperationType
from ralph.backends.data.clickhouse import ClickHouseDataBackend
from ralph.backends.data.mongo import MongoDataBackend

from tests.fixtures.backends import (
    CLICKHOUSE_TEST_DATABASE,
    CLICKHOUSE_TEST_HOST,
    CLICKHOUSE_TEST_PORT,
    CLICKHOUSE_TEST_TABLE_NAME,
    ES_TEST_INDEX,
    MONGO_TEST_COLLECTION,
    MONGO_TEST_DATABASE,
    get_async_es_test_backend,
    get_async_mongo_test_backend,
    get_clickhouse_test_backend,
    get_es_test_backend,
    get_mongo_test_backend,
)


def insert_es_statements(es_client, statements, index=ES_TEST_INDEX):
    """Insert a bunch of example statements into Elasticsearch for testing."""
    bulk(
        es_client,
        [
            {
                "_index": index,
                "_id": statement["id"],
                "_op_type": "index",
                "_source": statement,
            }
            for statement in statements
        ],
    )
    es_client.indices.refresh()


def insert_mongo_statements(mongo_client, statements, collection):
    """Insert a bunch of example statements into MongoDB for testing."""
    database = getattr(mongo_client, MONGO_TEST_DATABASE)
    collection = getattr(database, collection)
    collection.insert_many(
        list(
            MongoDataBackend.to_documents(
                data=statements,
                ignore_errors=True,
                operation_type=BaseOperationType.CREATE,
            )
        )
    )


def insert_clickhouse_statements(statements, table):
    """Insert a bunch of example statements into ClickHouse for testing."""
    settings = ClickHouseDataBackend.settings_class(
        HOST=CLICKHOUSE_TEST_HOST,
        PORT=CLICKHOUSE_TEST_PORT,
        DATABASE=CLICKHOUSE_TEST_DATABASE,
        EVENT_TABLE_NAME=CLICKHOUSE_TEST_TABLE_NAME,
    )
    backend = ClickHouseDataBackend(settings=settings)
    success = backend.write(statements, target=table)
    assert success == len(statements)


@pytest.fixture(params=["async_es", "async_mongo", "es", "mongo", "clickhouse"])
def insert_statements_and_monkeypatch_backend(
    request, es_custom, mongo_custom, clickhouse_custom, monkeypatch
):
    """(Security) Return a function that inserts statements into each backend."""

    def _insert_statements_and_monkeypatch_backend(statements, target=None):
        """Insert statements once into each backend."""
        backend_client_class_path = "ralph.api.routers.statements.BACKEND_CLIENT"
        if request.param == "async_es":
            target = target if target else ES_TEST_INDEX
            client = es_custom(index=target)
            insert_es_statements(client, statements, target)
            monkeypatch.setattr(backend_client_class_path, get_async_es_test_backend())
            return
        if request.param == "async_mongo":
            target = target if target else MONGO_TEST_COLLECTION
            client = mongo_custom(collection=target)
            insert_mongo_statements(client, statements, target)
            monkeypatch.setattr(
                backend_client_class_path, get_async_mongo_test_backend()
            )
            return
        if request.param == "es":
            target = target if target else ES_TEST_INDEX
            client = es_custom(index=target)
            insert_es_statements(client, statements, target)
            monkeypatch.setattr(backend_client_class_path, get_es_test_backend())
            return
        if request.param == "mongo":
            target = target if target else MONGO_TEST_COLLECTION
            client = mongo_custom(collection=target)
            insert_mongo_statements(client, statements, target)
            monkeypatch.setattr(backend_client_class_path, get_mongo_test_backend())
            return
        if request.param == "clickhouse":
            target = target if target else CLICKHOUSE_TEST_TABLE_NAME
            _ = clickhouse_custom(event_table_name=target)
            insert_clickhouse_statements(statements, target)
            monkeypatch.setattr(
                backend_client_class_path, get_clickhouse_test_backend()
            )
            return

    return _insert_statements_and_monkeypatch_backend
