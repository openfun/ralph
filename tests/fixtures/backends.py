"""Test fixtures for backends."""

import asyncio
import json
import os
import random
import time
from contextlib import asynccontextmanager
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

from ralph.backends.data.async_es import AsyncESDataBackend
from ralph.backends.data.async_mongo import AsyncMongoDataBackend
from ralph.backends.data.clickhouse import (
    ClickHouseClientOptions,
    ClickHouseDataBackend,
)
from ralph.backends.data.es import ESDataBackend
from ralph.backends.data.fs import FSDataBackend
from ralph.backends.data.ldp import LDPDataBackend
from ralph.backends.data.mongo import MongoDataBackend
from ralph.backends.data.s3 import S3DataBackend
from ralph.backends.data.swift import SwiftDataBackend
from ralph.backends.lrs.async_es import AsyncESLRSBackend
from ralph.backends.lrs.async_mongo import AsyncMongoLRSBackend
from ralph.backends.lrs.clickhouse import ClickHouseLRSBackend
from ralph.backends.lrs.es import ESLRSBackend
from ralph.backends.lrs.fs import FSLRSBackend
from ralph.backends.lrs.mongo import MongoLRSBackend
from ralph.conf import Settings, core_settings

# ClickHouse backend defaults
CLICKHOUSE_TEST_DATABASE = os.environ.get(
    "RALPH_BACKENDS__DATA__CLICKHOUSE__TEST_DATABASE", "test_statements"
)
CLICKHOUSE_TEST_HOST = os.environ.get(
    "RALPH_BACKENDS__DATA__CLICKHOUSE__TEST_HOST", "localhost"
)
CLICKHOUSE_TEST_PORT = os.environ.get(
    "RALPH_BACKENDS__DATA__CLICKHOUSE__TEST_PORT", 8123
)
CLICKHOUSE_TEST_TABLE_NAME = os.environ.get(
    "RALPH_BACKENDS__DATA__CLICKHOUSE__TEST_TABLE_NAME", "test_xapi_events_all"
)

# Elasticsearch backend defaults
ES_TEST_INDEX = os.environ.get("RALPH_BACKENDS__DATA__ES__TEST_INDEX", "test-index-foo")
ES_TEST_FORWARDING_INDEX = os.environ.get(
    "RALPH_BACKENDS__DATA__ES__TEST_FORWARDING_INDEX", "test-index-foo-2"
)
ES_TEST_INDEX_TEMPLATE = os.environ.get(
    "RALPH_BACKENDS__DATA__ES__INDEX_TEMPLATE", "test-index"
)
ES_TEST_INDEX_PATTERN = os.environ.get(
    "RALPH_BACKENDS__DATA__ES__TEST_INDEX_PATTERN", "test-index-*"
)
ES_TEST_HOSTS = os.environ.get(
    "RALPH_BACKENDS__DATA__ES__TEST_HOSTS", "http://localhost:9200"
).split(",")

# Mongo backend defaults
MONGO_TEST_COLLECTION = os.environ.get(
    "RALPH_BACKENDS__DATA__MONGO__TEST_COLLECTION", "marsha"
)
MONGO_TEST_FORWARDING_COLLECTION = os.environ.get(
    "RALPH_BACKENDS__DATA__MONGO__TEST_FORWARDING_COLLECTION", "marsha-2"
)
MONGO_TEST_DATABASE = os.environ.get(
    "RALPH_BACKENDS__DATA__MONGO__TEST_DATABASE", "statements"
)
MONGO_TEST_CONNECTION_URI = os.environ.get(
    "RALPH_BACKENDS__DATA__MONGO__TEST_CONNECTION_URI", "mongodb://localhost:27017/"
)

RUNSERVER_TEST_HOST = os.environ.get("RALPH_RUNSERVER_TEST_HOST", "0.0.0.0")
RUNSERVER_TEST_PORT = int(os.environ.get("RALPH_RUNSERVER_TEST_PORT", 8101))

# Websocket test backend defaults
WS_TEST_HOST = "localhost"
WS_TEST_PORT = 8765


@lru_cache()
def get_clickhouse_test_backend():
    """Return a ClickHouseLRSBackend backend instance using test defaults."""

    settings = ClickHouseLRSBackend.settings_class(
        HOST=CLICKHOUSE_TEST_HOST,
        PORT=CLICKHOUSE_TEST_PORT,
        DATABASE=CLICKHOUSE_TEST_DATABASE,
        EVENT_TABLE_NAME=CLICKHOUSE_TEST_TABLE_NAME,
    )
    return ClickHouseLRSBackend(settings)


@lru_cache
def get_es_test_backend():
    """Return a ESLRSBackend backend instance using test defaults."""
    settings = ESLRSBackend.settings_class(
        HOSTS=ES_TEST_HOSTS, DEFAULT_INDEX=ES_TEST_INDEX
    )
    return ESLRSBackend(settings)


@lru_cache
def get_async_es_test_backend(index: str = ES_TEST_INDEX):
    """Return an AsyncESLRSBackend backend instance using test defaults."""
    settings = AsyncESLRSBackend.settings_class(
        ALLOW_YELLOW_STATUS=False,
        CLIENT_OPTIONS={"ca_certs": None, "verify_certs": None},
        DEFAULT_INDEX=index,
        HOSTS=ES_TEST_HOSTS,
        LOCALE_ENCODING="utf8",
        POINT_IN_TIME_KEEP_ALIVE="1m",
        READ_CHUNK_SIZE=500,
        REFRESH_AFTER_WRITE=True,
        WRITE_CHUNK_SIZE=500,
    )
    return AsyncESLRSBackend(settings)


@lru_cache
def get_mongo_test_backend():
    """Return a MongoDatabase backend instance using test defaults."""
    settings = MongoLRSBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DEFAULT_DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    return MongoLRSBackend(settings)


@lru_cache
def get_async_mongo_test_backend(
    connection_uri: str = MONGO_TEST_CONNECTION_URI,
    default_collection: str = MONGO_TEST_COLLECTION,
    client_options: dict = None,
):
    """Return an AsyncMongoDatabase backend instance using test defaults."""
    settings = AsyncMongoLRSBackend.settings_class(
        CONNECTION_URI=connection_uri,
        DEFAULT_DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=default_collection,
        CLIENT_OPTIONS=client_options if client_options else {},
        LOCALE_ENCODING="utf8",
        READ_CHUNK_SIZE=500,
        WRITE_CHUNK_SIZE=500,
    )
    return AsyncMongoLRSBackend(settings)


def get_es_fixture(host=ES_TEST_HOSTS, index=ES_TEST_INDEX):
    """Create / delete an Elasticsearch test index and yield an instantiated client."""
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
    """Yield an Elasticsearch test client.

    See get_es_fixture above.
    """

    for es_client in get_es_fixture():
        yield es_client


@pytest.fixture
def es_forwarding():
    """Yield a second Elasticsearch test client.

    See get_es_fixture above.
    """
    for es_client in get_es_fixture(index=ES_TEST_FORWARDING_INDEX):
        yield es_client


@pytest.fixture
def fs_backend(fs, settings_fs):
    """Return the `get_fs_data_backend` function."""

    fs.create_dir("foo")

    def get_fs_data_backend(path: str = "foo"):
        """Return an instance of `FSDataBackend`."""
        settings = FSDataBackend.settings_class(
            DEFAULT_DIRECTORY_PATH=path,
            DEFAULT_QUERY_STRING="*",
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=1024,
            WRITE_CHUNK_SIZE=1024,
        )
        return FSDataBackend(settings)

    return get_fs_data_backend


@pytest.fixture
def fs_lrs_backend(fs, settings_fs):
    """Return the `get_fs_data_backend` function."""

    fs.create_dir("foo")

    def get_fs_lrs_backend(path: str = "foo"):
        """Return an instance of FSLRSBackend."""
        settings = FSLRSBackend.settings_class(
            DEFAULT_DIRECTORY_PATH=path,
            DEFAULT_QUERY_STRING="*",
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=1024,
            WRITE_CHUNK_SIZE=1024,
        )
        return FSLRSBackend(settings)

    return get_fs_lrs_backend


@pytest.fixture(scope="session")
def anyio_backend():
    """Select asyncio backend for pytest anyio."""
    return "asyncio"


@pytest.fixture
def async_mongo_backend():
    """Return the `get_mongo_data_backend` function."""

    def get_mongo_data_backend(
        connection_uri: str = MONGO_TEST_CONNECTION_URI,
        default_collection: str = MONGO_TEST_COLLECTION,
        client_options: dict = None,
    ):
        """Return an instance of `MongoDataBackend`."""
        settings = AsyncMongoDataBackend.settings_class(
            CONNECTION_URI=connection_uri,
            DEFAULT_DATABASE=MONGO_TEST_DATABASE,
            DEFAULT_COLLECTION=default_collection,
            CLIENT_OPTIONS=client_options if client_options else {},
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=500,
            WRITE_CHUNK_SIZE=500,
        )
        return AsyncMongoDataBackend(settings)

    return get_mongo_data_backend


@pytest.fixture
def async_mongo_lrs_backend():
    """Return the `get_async_mongo_test_backend` function."""

    get_async_mongo_test_backend.cache_clear()

    return get_async_mongo_test_backend


def get_mongo_fixture(
    connection_uri=MONGO_TEST_CONNECTION_URI,
    database=MONGO_TEST_DATABASE,
    collection=MONGO_TEST_COLLECTION,
):
    """Create / delete a Mongo test database + collection and yield an
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
    """Yield a Mongo test client.

    See get_mongo_fixture above.
    """
    for mongo_client in get_mongo_fixture():
        yield mongo_client


@pytest.fixture
def mongo_backend():
    """Return the `get_mongo_data_backend` function."""

    def get_mongo_data_backend(
        connection_uri: str = MONGO_TEST_CONNECTION_URI,
        default_collection: str = MONGO_TEST_COLLECTION,
        client_options: dict = None,
    ):
        """Return an instance of `MongoDataBackend`."""
        settings = MongoDataBackend.settings_class(
            CONNECTION_URI=connection_uri,
            DEFAULT_DATABASE=MONGO_TEST_DATABASE,
            DEFAULT_COLLECTION=default_collection,
            CLIENT_OPTIONS=client_options if client_options else {},
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=500,
            WRITE_CHUNK_SIZE=500,
        )
        return MongoDataBackend(settings)

    return get_mongo_data_backend


@pytest.fixture
def mongo_lrs_backend():
    """Return the `get_mongo_lrs_backend` function."""

    def get_mongo_lrs_backend(
        connection_uri: str = MONGO_TEST_CONNECTION_URI,
        default_collection: str = MONGO_TEST_COLLECTION,
        client_options: dict = None,
    ):
        """Return an instance of MongoLRSBackend."""
        settings = MongoLRSBackend.settings_class(
            CONNECTION_URI=connection_uri,
            DEFAULT_DATABASE=MONGO_TEST_DATABASE,
            DEFAULT_COLLECTION=default_collection,
            CLIENT_OPTIONS=client_options if client_options else {},
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=500,
            WRITE_CHUNK_SIZE=500,
        )
        return MongoLRSBackend(settings)

    return get_mongo_lrs_backend


@pytest.fixture
def mongo_forwarding():
    """Yield a second Mongo test client.

    See get_mongo_fixture above.
    """
    for mongo_client in get_mongo_fixture(collection=MONGO_TEST_FORWARDING_COLLECTION):
        yield mongo_client


def get_clickhouse_fixture(
    host=CLICKHOUSE_TEST_HOST,
    port=CLICKHOUSE_TEST_PORT,
    database=CLICKHOUSE_TEST_DATABASE,
    event_table_name=CLICKHOUSE_TEST_TABLE_NAME,
):
    """Create / delete a ClickHouse test database + table and yield an
    instantiated client.
    """
    client_options = ClickHouseClientOptions(
        date_time_input_format="best_effort",  # Allows RFC dates
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
        CREATE TABLE {event_table_name} (
        event_id UUID NOT NULL,
        emission_time DateTime64(6) NOT NULL,
        event String NOT NULL
        )
        ENGINE MergeTree ORDER BY (emission_time, event_id)
        PRIMARY KEY (emission_time, event_id)
    """

    client.command(sql)
    yield client
    client.command(f"DROP DATABASE {database}")


@pytest.fixture
def clickhouse():
    """Yield a ClickHouse test client.

    See get_clickhouse_fixture above.
    """
    for clickhouse_client in get_clickhouse_fixture():
        yield clickhouse_client


@pytest.fixture
def es_data_stream():
    """Create / delete an Elasticsearch test datastream and yield an instantiated
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
            # Note: We define an explicit mapping of the `timestamp` field to allow
            # the Elasticsearch database to be queried even if no document has
            # been inserted before.
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
    """Force Path instantiation with fake FS in ralph settings."""

    monkeypatch.setattr(
        "ralph.backends.data.mixins.settings",
        Settings(HISTORY_FILE=Path(core_settings.APP_DIR / "history.json")),
    )


@pytest.fixture
def ldp_backend(settings_fs):
    """Return the `get_ldp_data_backend` function."""

    def get_ldp_data_backend(service_name: str = "foo", stream_id: str = "bar"):
        """Return an instance of LDPDataBackend."""
        settings = LDPDataBackend.settings_class(
            APPLICATION_KEY="fake_key",
            APPLICATION_SECRET="fake_secret",
            CONSUMER_KEY="another_fake_key",
            DEFAULT_STREAM_ID=stream_id,
            ENDPOINT="ovh-eu",
            SERVICE_NAME=service_name,
            REQUEST_TIMEOUT=None,
            READ_CHUNK_SIZE=500,
            WRITE_CHUNK_SIZE=500,
        )
        return LDPDataBackend(settings)

    return get_ldp_data_backend


@pytest.fixture
def async_es_backend():
    """Return the `get_async_es_data_backend` function."""

    def get_async_es_data_backend():
        """Return an instance of AsyncESDataBackend."""
        settings = AsyncESDataBackend.settings_class(
            ALLOW_YELLOW_STATUS=False,
            CLIENT_OPTIONS={"ca_certs": None, "verify_certs": None},
            DEFAULT_INDEX=ES_TEST_INDEX,
            HOSTS=ES_TEST_HOSTS,
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=500,
            REFRESH_AFTER_WRITE=True,
            WRITE_CHUNK_SIZE=500,
        )
        return AsyncESDataBackend(settings)

    return get_async_es_data_backend


@pytest.fixture
def async_es_lrs_backend():
    """Return the `get_async_es_test_backend` function."""

    get_async_es_test_backend.cache_clear()

    return get_async_es_test_backend


@pytest.fixture
def clickhouse_backend():
    """Return the `get_clickhouse_data_backend` function."""

    def get_clickhouse_data_backend():
        """Return an instance of ClickHouseDataBackend."""
        settings = ClickHouseDataBackend.settings_class(
            HOST=CLICKHOUSE_TEST_HOST,
            PORT=CLICKHOUSE_TEST_PORT,
            DATABASE=CLICKHOUSE_TEST_DATABASE,
            EVENT_TABLE_NAME=CLICKHOUSE_TEST_TABLE_NAME,
            USERNAME="default",
            PASSWORD="",
            CLIENT_OPTIONS={
                "date_time_input_format": "best_effort",
            },
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=500,
            WRITE_CHUNK_SIZE=500,
        )
        return ClickHouseDataBackend(settings)

    return get_clickhouse_data_backend


@pytest.fixture
def clickhouse_lrs_backend():
    """Return the `get_clickhouse_lrs_backend` function."""

    def get_clickhouse_lrs_backend():
        """Return an instance of ClickHouseLRSBackend."""
        settings = ClickHouseLRSBackend.settings_class(
            HOST=CLICKHOUSE_TEST_HOST,
            PORT=CLICKHOUSE_TEST_PORT,
            DATABASE=CLICKHOUSE_TEST_DATABASE,
            EVENT_TABLE_NAME=CLICKHOUSE_TEST_TABLE_NAME,
            USERNAME="default",
            PASSWORD="",
            CLIENT_OPTIONS={
                "date_time_input_format": "best_effort",
            },
            LOCALE_ENCODING="utf8",
            IDS_CHUNK_SIZE=10000,
            READ_CHUNK_SIZE=500,
            WRITE_CHUNK_SIZE=500,
        )
        return ClickHouseLRSBackend(settings)

    return get_clickhouse_lrs_backend


@pytest.fixture
def es_backend():
    """Return the `get_es_data_backend` function."""

    def get_es_data_backend():
        """Return an instance of ESDataBackend."""
        settings = ESDataBackend.settings_class(
            ALLOW_YELLOW_STATUS=False,
            CLIENT_OPTIONS={"ca_certs": None, "verify_certs": None},
            DEFAULT_INDEX=ES_TEST_INDEX,
            HOSTS=ES_TEST_HOSTS,
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=500,
            REFRESH_AFTER_WRITE=True,
            WRITE_CHUNK_SIZE=500,
        )
        return ESDataBackend(settings)

    return get_es_data_backend


@pytest.fixture
def es_lrs_backend():
    """Return the `get_es_lrs_backend` function."""

    def get_es_lrs_backend(index: str = ES_TEST_INDEX):
        """Return an instance of ESLRSBackend."""
        settings = ESLRSBackend.settings_class(
            ALLOW_YELLOW_STATUS=False,
            CLIENT_OPTIONS={"ca_certs": None, "verify_certs": None},
            DEFAULT_INDEX=index,
            HOSTS=ES_TEST_HOSTS,
            LOCALE_ENCODING="utf8",
            POINT_IN_TIME_KEEP_ALIVE="1m",
            READ_CHUNK_SIZE=500,
            REFRESH_AFTER_WRITE=True,
            WRITE_CHUNK_SIZE=500,
        )
        return ESLRSBackend(settings)

    return get_es_lrs_backend


@pytest.fixture
def swift_backend():
    """Return get_swift_data_backend function."""

    def get_swift_data_backend():
        """Return an instance of SwiftDataBackend."""
        settings = SwiftDataBackend.settings_class(
            AUTH_URL="https://auth.cloud.ovh.net/",
            USERNAME="os_username",
            PASSWORD="os_password",
            IDENTITY_API_VERSION="3",
            TENANT_ID="os_tenant_id",
            TENANT_NAME="os_tenant_name",
            PROJECT_DOMAIN_NAME="Default",
            REGION_NAME="os_region_name",
            OBJECT_STORAGE_URL="os_storage_url/ralph_logs_container",
            USER_DOMAIN_NAME="Default",
            DEFAULT_CONTAINER="container_name",
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=500,
            WRITE_CHUNK_SIZE=500,
        )
        return SwiftDataBackend(settings)

    return get_swift_data_backend


@pytest.fixture()
def moto_fs(fs):
    """Fix the incompatibility between moto and pyfakefs."""

    for module in [boto3, botocore]:
        module_dir = Path(module.__file__).parent
        fs.add_real_directory(module_dir, lazy_read=False)


@pytest.fixture
def s3_backend():
    """Return the `get_s3_data_backend` function."""

    def get_s3_data_backend():
        """Return an instance of S3DataBackend."""
        settings = S3DataBackend.settings_class(
            ACCESS_KEY_ID="access_key_id",
            SECRET_ACCESS_KEY="secret_access_key",
            SESSION_TOKEN="session_token",
            ENDPOINT_URL=None,
            DEFAULT_REGION="default-region",
            DEFAULT_BUCKET_NAME="bucket_name",
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=4096,
            WRITE_CHUNK_SIZE=4096,
        )
        return S3DataBackend(settings)

    return get_s3_data_backend


@pytest.fixture
def events():
    """Return test events fixture."""
    return [{"id": idx} for idx in range(10)]


@pytest.fixture
def ws(events):
    """Return a websocket server instance."""

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def forward(websocket, path):
        """Stupid test server that sends events."""

        for event in events:
            await websocket.send(json.dumps(event))
            time.sleep(random.randrange(0, 500) / 10000.0)

    server = websockets.serve(forward, "0.0.0.0", WS_TEST_PORT)
    asyncio.get_event_loop().run_until_complete(server)
    yield server

    server.ws_server.close()

    asyncio.get_event_loop().run_until_complete(server.ws_server.wait_closed())
    loop.close()


@pytest.fixture
def lrs():
    """Return a context manager that runs ralph's lrs server."""

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
