"""Test fixtures for backends."""

import asyncio
import json
import os
import random
from contextlib import asynccontextmanager
from functools import lru_cache, wraps
from multiprocessing import Process
from pathlib import Path
from typing import Callable, Optional, Union

import boto3
import botocore
import clickhouse_connect
import pytest
import uvicorn
import websockets
from elasticsearch import BadRequestError, Elasticsearch
from httpx import AsyncClient, ConnectError
from pydantic import AnyHttpUrl, TypeAdapter
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid

from websockets.asyncio.server import serve

from ralph.backends.data.async_es import AsyncESDataBackend
from ralph.backends.data.async_lrs import AsyncLRSDataBackend
from ralph.backends.data.async_mongo import AsyncMongoDataBackend
from ralph.backends.data.clickhouse import (
    ClickHouseClientOptions,
    ClickHouseDataBackend,
)
from ralph.backends.data.es import ESDataBackend
from ralph.backends.data.fs import FSDataBackend
from ralph.backends.data.ldp import LDPDataBackend
from ralph.backends.data.lrs import LRSDataBackend, LRSHeaders
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
        REFRESH_AFTER_WRITE="true",
        WRITE_CHUNK_SIZE=499,
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
        WRITE_CHUNK_SIZE=499,
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
def es_custom():
    """Yield `_es_custom` function."""

    teardown = []
    client = Elasticsearch(ES_TEST_HOSTS)

    def _es_custom(host=ES_TEST_HOSTS, index=ES_TEST_INDEX):
        """Create the index and yield an Elasticsearch test client."""
        try:
            client.indices.create(index=index)
        except BadRequestError:
            # The index might already exist
            client.indices.delete(index=index)
            client.indices.create(index=index)
        teardown.append(index)
        return client

    yield _es_custom

    for index in teardown:
        client.indices.delete(index=index)
    client.close()


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
            WRITE_CHUNK_SIZE=999,
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
            DEFAULT_DIRECTORY_PATH=Path(path),
            DEFAULT_QUERY_STRING="*",
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=1024,
            WRITE_CHUNK_SIZE=999,
        )
        return FSLRSBackend(settings)

    return get_fs_lrs_backend


@pytest.fixture(scope="session")
def anyio_backend():
    """Select asyncio backend for pytest anyio."""
    return "asyncio"


@pytest.fixture(params=["sync", "async"])
def flavor(request):
    """Parametrize fixture with `sync`/`async` flavor."""
    return request.param


@pytest.mark.anyio
@pytest.fixture
def lrs_backend(
    flavor,
) -> Callable[[Optional[str]], Union[LRSDataBackend, AsyncLRSDataBackend]]:
    """Return the `get_lrs_test_backend` function."""
    backend_class = LRSDataBackend if flavor == "sync" else AsyncLRSDataBackend

    def make_awaitable(sync_func):
        """Make a synchronous callable awaitable."""

        @wraps(sync_func)
        async def async_func(*args, **kwargs):
            kwargs.pop("concurrency", None)
            return sync_func(*args, **kwargs)

        return async_func

    def make_awaitable_generator(sync_func):
        """Make a synchronous generator awaitable."""

        @wraps(sync_func)
        async def async_func(*args, **kwargs):
            kwargs.pop("prefetch", None)
            for item in sync_func(*args, **kwargs):
                yield item

        return async_func

    def _get_lrs_test_backend(
        base_url: Optional[str] = "http://fake-lrs.com",
    ) -> Union[LRSDataBackend, AsyncLRSDataBackend]:
        """Return an (Async)LRSDataBackend backend instance using test defaults."""
        headers = {
            "X_EXPERIENCE_API_VERSION": "1.0.3",
            "CONTENT_TYPE": "application/json",
        }
        settings = backend_class.settings_class(
            BASE_URL=TypeAdapter(AnyHttpUrl).validate_python(base_url),
            USERNAME="user",
            PASSWORD="pass",
            HEADERS=LRSHeaders.model_validate(headers),
            LOCALE_ENCODING="utf8",
            STATUS_ENDPOINT="/__heartbeat__",
            STATEMENTS_ENDPOINT="/xAPI/statements/",
            READ_CHUNK_SIZE=500,
            WRITE_CHUNK_SIZE=500,
        )
        backend = backend_class(settings)

        if isinstance(backend, LRSDataBackend):
            backend.status = make_awaitable(backend.status)  # type: ignore
            backend.read = make_awaitable_generator(backend.read)  # type: ignore
            backend.write = make_awaitable(backend.write)  # type: ignore
            backend.close = make_awaitable(backend.close)  # type: ignore

        return backend

    return _get_lrs_test_backend


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
            WRITE_CHUNK_SIZE=499,
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
def mongo_custom():
    """Yield `_mongo_custom` function."""

    teardown = []

    client = MongoClient(MONGO_TEST_CONNECTION_URI)
    database = getattr(client, MONGO_TEST_DATABASE)

    def _mongo_custom(collection=MONGO_TEST_COLLECTION):
        """Create the collection and yield the Mongo test client."""
        try:
            database.create_collection(collection)
        except CollectionInvalid:
            # The collection might already exist
            database.drop_collection(collection)
            database.create_collection(collection)
        teardown.append(collection)
        return client

    yield _mongo_custom

    for collection in teardown:
        database.drop_collection(collection)
    client.drop_database(database)
    client.close()


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
            WRITE_CHUNK_SIZE=499,
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
            WRITE_CHUNK_SIZE=499,
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
    ).model_dump()

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
def clickhouse_custom():
    """Return the `_clickhouse_custom` function."""

    teardown = []

    host = CLICKHOUSE_TEST_HOST
    port = CLICKHOUSE_TEST_PORT
    database = CLICKHOUSE_TEST_DATABASE

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
    client_db = clickhouse_connect.get_client(
        host=host,
        port=port,
        database=database,
        settings=client_options,
    )

    def _clickhouse_custom(
        host=CLICKHOUSE_TEST_HOST,
        port=CLICKHOUSE_TEST_PORT,
        database=CLICKHOUSE_TEST_DATABASE,
        event_table_name=CLICKHOUSE_TEST_TABLE_NAME,
    ):
        """Create / delete a ClickHouse test database + table and yield an
        instantiated client.
        """

        sql = f"DROP TABLE IF EXISTS {event_table_name}"
        client_db.command(sql)

        sql = f"""
            CREATE TABLE {event_table_name} (
            event_id UUID NOT NULL,
            emission_time DateTime64(6) NOT NULL,
            event String NOT NULL
            )
            ENGINE MergeTree ORDER BY (emission_time, event_id)
            PRIMARY KEY (emission_time, event_id)
        """

        client_db.command(sql)
        teardown.append((client_db, event_table_name))
        return client_db

    yield _clickhouse_custom

    for client_db, table in teardown:
        client_db.command(f"DROP TABLE IF EXISTS {table}")

    client.command(f"DROP DATABASE IF EXISTS {database}")


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
            WRITE_CHUNK_SIZE=499,
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
            REFRESH_AFTER_WRITE="true",
            WRITE_CHUNK_SIZE=499,
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
            WRITE_CHUNK_SIZE=499,
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
            WRITE_CHUNK_SIZE=499,
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
            REFRESH_AFTER_WRITE="true",
            WRITE_CHUNK_SIZE=499,
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
            REFRESH_AFTER_WRITE="true",
            WRITE_CHUNK_SIZE=499,
        )
        return ESLRSBackend(settings)

    return get_es_lrs_backend


@pytest.fixture
def swift_backend():
    """Return get_swift_data_backend function."""

    def get_swift_data_backend(container: str = "container_name"):
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
            DEFAULT_CONTAINER=container,
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=500,
            WRITE_CHUNK_SIZE=499,
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

    def get_s3_data_backend(bucket_name: str = "bucket_name"):
        """Return an instance of S3DataBackend."""
        settings = S3DataBackend.settings_class(
            ACCESS_KEY_ID="access_key_id",
            SECRET_ACCESS_KEY="secret_access_key",
            SESSION_TOKEN="session_token",
            ENDPOINT_URL=None,
            DEFAULT_REGION="default-region",
            DEFAULT_BUCKET_NAME=bucket_name,
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=4096,
            WRITE_CHUNK_SIZE=3999,
        )
        return S3DataBackend(settings)

    return get_s3_data_backend


@pytest.fixture
def events():
    """Return test events fixture."""
    return [{"id": idx} for idx in range(10)]


@pytest.mark.anyio
@pytest.fixture
async def ws(events):
    """Return a websocket server instance."""

    async def forward(websocket):
        """Stupid test server that sends events."""
        for event in events:
            await websocket.send(json.dumps(event))
            await asyncio.sleep(random.randrange(0, 500) / 10000.0)

    async with serve(forward, "0.0.0.0", WS_TEST_PORT) as server:
        yield server


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
