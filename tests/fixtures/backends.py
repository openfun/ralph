"""Test fixtures for backends."""

import asyncio
import json
import os
import random
import time
from contextlib import asynccontextmanager
from enum import Enum
from functools import lru_cache
from multiprocessing import Process
from pathlib import Path

import boto3
import botocore
import clickhouse_connect
import pytest
import uvicorn
import websockets
from elasticsearch import BadRequestError, Elasticsearch
from httpx import AsyncClient, ConnectError
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid

from ralph.backends.database.clickhouse import ClickHouseDatabase
from ralph.backends.database.es import ESDatabase
from ralph.backends.database.mongo import MongoDatabase
from ralph.backends.storage.s3 import S3Storage
from ralph.backends.storage.swift import SwiftStorage
from ralph.conf import ClickhouseClientOptions, Settings, settings

# ClickHouse backend defaults
CLICKHOUSE_TEST_DATABASE = os.environ.get(
    "RALPH_BACKENDS__DATABASE__CLICKHOUSE__TEST_DATABASE", "test_statements"
)
CLICKHOUSE_TEST_HOST = os.environ.get(
    "RALPH_BACKENDS__DATABASE__CLICKHOUSE__TEST_HOST", "localhost"
)
CLICKHOUSE_TEST_PORT = os.environ.get(
    "RALPH_BACKENDS__DATABASE__CLICKHOUSE__TEST_PORT", 8123
)
CLICKHOUSE_TEST_TABLE_NAME = os.environ.get(
    "RALPH_BACKENDS__DATABASE__CLICKHOUSE__TEST_TABLE_NAME", "test_xapi_events_all"
)

# Elasticsearch backend defaults
ES_TEST_INDEX = os.environ.get(
    "RALPH_BACKENDS__DATABASE__ES__TEST_INDEX", "test-index-foo"
)
ES_TEST_FORWARDING_INDEX = os.environ.get(
    "RALPH_BACKENDS__DATABASE__ES__TEST_FORWARDING_INDEX", "test-index-foo-2"
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

# Mongo backend defaults
MONGO_TEST_COLLECTION = os.environ.get(
    "RALPH_BACKENDS__DATABASE__MONGO__TEST_COLLECTION", "marsha"
)
MONGO_TEST_FORWARDING_COLLECTION = os.environ.get(
    "RALPH_BACKENDS__DATABASE__MONGO__TEST_FORWARDING_COLLECTION", "marsha-2"
)
MONGO_TEST_DATABASE = os.environ.get(
    "RALPH_BACKENDS__DATABASE__MONGO__TEST_DATABASE", "statements"
)
MONGO_TEST_CONNECTION_URI = os.environ.get(
    "RALPH_BACKENDS__DATABASE__MONGO__TEST_CONNECTION_URI", "mongodb://localhost:27017/"
)

RUNSERVER_TEST_HOST = os.environ.get("RALPH_RUNSERVER_TEST_HOST", "0.0.0.0")
RUNSERVER_TEST_PORT = int(os.environ.get("RALPH_RUNSERVER_TEST_PORT", 8101))

# Websocket test backend defaults
WS_TEST_HOST = "localhost"
WS_TEST_PORT = 8765


@lru_cache()
def get_clickhouse_test_backend():
    """Returns a ClickHouseDatabase backend instance using test defaults."""
    return ClickHouseDatabase(
        host=CLICKHOUSE_TEST_HOST,
        port=CLICKHOUSE_TEST_PORT,
        database=CLICKHOUSE_TEST_DATABASE,
        event_table_name=CLICKHOUSE_TEST_TABLE_NAME,
    )


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
def es_forwarding():
    """Yields a second ElasticSearch test client. See get_es_fixture above."""
    for es_client in get_es_fixture(index=ES_TEST_FORWARDING_INDEX):
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
def mongo_forwarding():
    """Yields a second Mongo test client. See get_mongo_fixture above."""
    for mongo_client in get_mongo_fixture(collection=MONGO_TEST_FORWARDING_COLLECTION):
        yield mongo_client


def get_clickhouse_fixture(
    host=CLICKHOUSE_TEST_HOST,
    port=CLICKHOUSE_TEST_PORT,
    database=CLICKHOUSE_TEST_DATABASE,
    event_table_name=CLICKHOUSE_TEST_TABLE_NAME,
):
    """Creates / deletes a ClickHouse test database + table and yields an
    instantiated client.
    """
    client_options = ClickhouseClientOptions(
        date_time_input_format="best_effort",  # Allows RFC dates
        allow_experimental_object_type=1,  # Allows JSON data type
    ).dict()

    client = clickhouse_connect.get_client(
        host=host,
        port=port,
        settings=client_options,
    )

    sql = f"""CREATE DATABASE IF NOT EXISTS {database}"""
    client.command(sql)

    # Now get a client with the correct database
    client = clickhouse_connect.get_client(
        host=host,
        port=port,
        database=database,
        settings=client_options,
    )

    sql = f"""DROP TABLE IF EXISTS {event_table_name}"""
    client.command(sql)

    sql = f"""
        CREATE TABLE IF NOT EXISTS {event_table_name} (
        event_id UUID NOT NULL,
        emission_time DateTime64(6) NOT NULL,
        event JSON NOT NULL,
        event_str String NOT NULL
        )
        ENGINE MergeTree ORDER BY (emission_time, event_id)
        PRIMARY KEY (emission_time, event_id)
    """

    client.command(sql)
    yield client
    client.command(f"DROP DATABASE {database}")


@pytest.fixture
def clickhouse():
    """Yields a ClickHouse test client. See get_clickhouse_fixture above."""
    for clickhouse_client in get_clickhouse_fixture():
        yield clickhouse_client


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
def settings_fs(fs, monkeypatch):
    """Forces Path instantiation with fake FS in Ralph's Settings."""
    # pylint:disable=invalid-name,unused-argument

    monkeypatch.setattr(
        "ralph.backends.mixins.settings",
        Settings(HISTORY_FILE=Path(settings.APP_DIR / "history.json")),
    )


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


@pytest.fixture()
def moto_fs(fs):
    """Fix the incompatibility between moto and pyfakefs"""
    # pylint:disable=invalid-name

    for module in [boto3, botocore]:
        module_dir = Path(module.__file__).parent
        fs.add_real_directory(module_dir, lazy_read=False)


@pytest.fixture
def s3():
    """Returns get_s3_storage function."""
    # pylint:disable=invalid-name

    def get_s3_storage():
        """Returns an instance of S3Storage."""

        return S3Storage(
            access_key_id="access_key_id",
            secret_access_key="secret_access_key",
            session_token="session_token",
            default_region="default-region",
            bucket_name="bucket_name",
            endpoint_url=None,
        )

    return get_s3_storage


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


@pytest.fixture
def lrs():
    """Returns a context manager that runs ralph's lrs server."""
    # pylint: disable=invalid-name,redefined-outer-name

    @asynccontextmanager
    async def runserver(app, host=RUNSERVER_TEST_HOST, port=RUNSERVER_TEST_PORT):
        process = Process(
            target=uvicorn.run,
            args=(app,),
            kwargs={"host": host, "port": port, "log_level": "debug"},
            daemon=True,
        )
        try:
            process.start()
            async with AsyncClient() as client:
                server_ready = False
                while not server_ready:
                    try:
                        response = await client.get(f"http://{host}:{port}/whoami")
                        assert response.status_code == 401
                        server_ready = True
                    except ConnectError:
                        await asyncio.sleep(0.1)
            yield process
        finally:
            process.terminate()

    return runserver
