"""Test fixtures for backends"""

import asyncio
import json
import os
import random
import time
from enum import Enum
from functools import lru_cache

import pytest
import websockets
from elasticsearch import BadRequestError, Elasticsearch
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid

from ralph.backends.database.es import ESDatabase
from ralph.backends.database.mongo import MongoDatabase
from ralph.backends.storage.swift import SwiftStorage

# Elasticsearch backend defaults
ES_TEST_INDEX = os.environ.get(
    "RALPH_BACKENDS__DATABASE__ES__TEST_INDEX", "test-index-foo"
)
ES_TEST_INDEX_2 = os.environ.get(
    "RALPH_BACKENDS__DATABASE__ES__TEST_INDEX_2", "test-index-foo-2"
)
ES_TEST_INDEX_TEMPLATE = os.environ.get(
    "RALPH_BACKENDS__DATABASE__ES__INDEX_TEMPLATE", "test-index"
)
ES_TEST_INDEX_PATTERN = os.environ.get(
    "RALPH_BACKENDS__DATABASE__ES__TEST_INDEX_PATTERN", "test-index-*"
)
ES_TEST_HOSTS = os.environ.get(
    "RALPH_BACKENDS__DATABASE__ES__TEST_HOSTS", "http://localhost:9200"
).split(",")

MONGO_TEST_COLLECTION = os.environ.get(
    "RALPH_BACKENDS__DATABASE__MONGO__TEST_COLLECTION", "marsha"
)
MONGO_TEST_COLLECTION_2 = os.environ.get(
    "RALPH_BACKENDS__DATABASE__MONGO__TEST_COLLECTION_2", "marsha-2"
)
MONGO_TEST_DATABASE = os.environ.get(
    "RALPH_BACKENDS__DATABASE__MONGO__TEST_DATABASE", "statements"
)
MONGO_TEST_CONNECTION_URI = os.environ.get(
    "RALPH_BACKENDS__DATABASE__MONGO__TEST_CONNECTION_URI", "mongodb://localhost:27017/"
)

# Websocket test backend defaults
WS_TEST_HOST = "localhost"
WS_TEST_PORT = 8765


@lru_cache
def get_es_test_backend():
    """Returns a ESDatabase backend instance using test defaults."""

    return ESDatabase(hosts=ES_TEST_HOSTS, index=ES_TEST_INDEX)


@lru_cache
def get_mongo_test_backend():
    """Returns a MongoDatabase backend instance using test defaults."""

    return MongoDatabase(
        connection_uri=MONGO_TEST_CONNECTION_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )


class NamedClassA:
    """An example named class."""

    name = "A"


class NamedClassB:
    """A second example named class."""

    name = "B"


class NamedClassEnum(Enum):
    """A named test classes Enum."""

    A = "tests.fixtures.backends.NamedClassA"
    B = "tests.fixtures.backends.NamedClassB"


def get_es_fixture(host=ES_TEST_HOSTS, index=ES_TEST_INDEX):
    """Creates / deletes an ElasticSearch test index and yields an instantiated
    client.
    """

    client = Elasticsearch(host)
    try:
        client.indices.create(index=index)
    except BadRequestError:
        # The index might already exist
        client.indices.delete(index=index)
        client.indices.create(index=index)
    yield client
    client.indices.delete(index=index)


@pytest.fixture
def es():
    """Yields an ElasticSearch test client. See get_es_fixture above."""
    # pylint: disable=invalid-name

    for es_client in get_es_fixture():
        yield es_client


@pytest.fixture
def es2():
    """Yields a second ElasticSearch test client. See get_es_fixture above."""

    for es_client in get_es_fixture(index=ES_TEST_INDEX_2):
        yield es_client


def get_mongo_fixture(
    connection_uri=MONGO_TEST_CONNECTION_URI,
    database=MONGO_TEST_DATABASE,
    collection=MONGO_TEST_COLLECTION,
):
    """Creates / deletes a Mongo test database + collection and yields an
    instantiated client.
    """

    client = MongoClient(connection_uri)
    database = getattr(client, database)
    try:
        database.create_collection(collection)
    except CollectionInvalid:
        # The collection might already exist
        database.drop_collection(collection)
        database.create_collection(collection)
    yield client
    database.drop_collection(collection)
    client.drop_database(database)


@pytest.fixture
def mongo():
    """Yields a Mongo test client. See get_mongo_fixture above."""

    for mongo_client in get_mongo_fixture():
        yield mongo_client


@pytest.fixture
def mongo2():
    """Yields a second Mongo test client. See get_mongo_fixture above."""

    for mongo_client in get_mongo_fixture(collection=MONGO_TEST_COLLECTION_2):
        yield mongo_client


@pytest.fixture
def es_data_stream():
    """Creates / deletes an ElasticSearch test datastream and yields an instantiated
    client.
    """

    client = Elasticsearch(ES_TEST_HOSTS)

    # Create statements index template with enabled data stream
    index_patterns = [ES_TEST_INDEX_PATTERN]
    data_stream = {}
    template = {
        "mappings": {
            "dynamic": True,
            "dynamic_date_formats": [
                "strict_date_optional_time",
                "yyyy/MM/dd HH:mm:ss Z||yyyy/MM/dd Z",
            ],
            "dynamic_templates": [],
            "date_detection": True,
            "numeric_detection": True,
            # Note: We define an explicit mapping of the `timestamp` field to allow the
            # ElasticSearch database to be queried even if no document has been inserted
            # before.
            "properties": {
                "timestamp": {
                    "type": "date",
                    "index": True,
                }
            },
        },
        "settings": {
            "index": {
                "number_of_shards": "1",
                "number_of_replicas": "1",
            }
        },
    }
    client.indices.put_index_template(
        name=ES_TEST_INDEX_TEMPLATE,
        index_patterns=index_patterns,
        data_stream=data_stream,
        template=template,
    )

    # Create a datastream matching the index template
    client.indices.create_data_stream(name=ES_TEST_INDEX)

    yield client

    client.indices.delete_data_stream(name=ES_TEST_INDEX)
    client.indices.delete_index_template(name=ES_TEST_INDEX_TEMPLATE)


@pytest.fixture
def swift():
    """Returns get_swift_storage function."""

    def get_swift_storage():
        """Returns an instance of SwiftStorage."""

        return SwiftStorage(
            os_tenant_id="os_tenant_id",
            os_tenant_name="os_tenant_name",
            os_username="os_username",
            os_password="os_password",
            os_region_name="os_region_name",
            os_storage_url="os_storage_url/ralph_logs_container",
        )

    return get_swift_storage


@pytest.fixture
def events():
    """Returns test events fixture."""
    return [{"id": idx} for idx in range(10)]


@pytest.fixture
def ws(events):
    """Returns a websocket server instance."""
    # pylint: disable=invalid-name,redefined-outer-name

    async def forward(websocket, path):
        """Stupid test server that sends events."""
        # pylint: disable=unused-argument

        for event in events:
            await websocket.send(json.dumps(event))
            time.sleep(random.randrange(0, 500) / 10000.0)

    # pylint: disable=no-member
    server = websockets.serve(forward, "0.0.0.0", WS_TEST_PORT)
    asyncio.get_event_loop().run_until_complete(server)
    yield server

    server.ws_server.close()
