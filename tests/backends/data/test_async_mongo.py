"""Tests for Ralph's async mongo data backend."""

import json
import logging
import re

import pytest
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, PyMongoError

from ralph.backends.data.async_mongo import (
    AsyncMongoDataBackend,
    MongoDataBackendSettings,
    MongoQuery,
)
from ralph.backends.data.base import AsyncWritable, BaseOperationType, DataBackendStatus
from ralph.backends.data.mongo import MongoClientOptions
from ralph.exceptions import BackendException, BackendParameterException

from tests.fixtures.backends import (
    MONGO_TEST_COLLECTION,
    MONGO_TEST_CONNECTION_URI,
    MONGO_TEST_DATABASE,
)


@pytest.mark.anyio
async def test_backends_data_async_mongo_default_instantiation(monkeypatch, fs):
    """Test the `AsyncMongoDataBackend` default instantiation."""

    fs.create_file(".env")
    backend_settings_names = [
        "CONNECTION_URI",
        "DEFAULT_DATABASE",
        "DEFAULT_COLLECTION",
        "CLIENT_OPTIONS",
        "LOCALE_ENCODING",
        "READ_CHUNK_SIZE",
        "WRITE_CHUNK_SIZE",
    ]
    for name in backend_settings_names:
        monkeypatch.delenv(f"RALPH_BACKENDS__DATA__MONGO__{name}", raising=False)

    assert AsyncMongoDataBackend.name == "async_mongo"
    assert AsyncMongoDataBackend.query_class == MongoQuery
    assert AsyncMongoDataBackend.default_operation_type == BaseOperationType.INDEX
    assert AsyncMongoDataBackend.settings_class == MongoDataBackendSettings
    backend = AsyncMongoDataBackend()
    assert isinstance(backend.client, AsyncIOMotorClient)
    assert backend.database.name == "statements"
    assert backend.collection.name == "marsha"
    assert backend.settings.CONNECTION_URI == "mongodb://localhost:27017/"
    assert backend.settings.CLIENT_OPTIONS == MongoClientOptions()
    assert backend.settings.LOCALE_ENCODING == "utf8"
    assert backend.settings.READ_CHUNK_SIZE == 500
    assert backend.settings.WRITE_CHUNK_SIZE == 500

    # Test overriding default values with environment variables.
    monkeypatch.setenv("RALPH_BACKENDS__DATA__MONGO__CLIENT_OPTIONS__tz_aware", True)
    backend = AsyncMongoDataBackend()
    assert backend.settings.CLIENT_OPTIONS == MongoClientOptions(tz_aware=True)
    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_mongo_instantiation_with_settings(
    async_mongo_backend,
):
    """Test the `AsyncMongoDataBackend` instantiation with settings."""
    backend = async_mongo_backend(default_collection="foo")
    assert backend.database.name == MONGO_TEST_DATABASE
    assert backend.collection.name == "foo"
    assert backend.settings.CONNECTION_URI == MONGO_TEST_CONNECTION_URI
    assert backend.settings.CLIENT_OPTIONS == MongoClientOptions()
    assert backend.settings.LOCALE_ENCODING == "utf8"
    assert backend.settings.READ_CHUNK_SIZE == 500
    assert backend.settings.WRITE_CHUNK_SIZE == 499


@pytest.mark.anyio
async def test_backends_data_async_mongo_status_with_connection_failure(
    async_mongo_backend, monkeypatch, caplog
):
    """Test the `AsyncMongoDataBackend.status` method, given a connection failure,
    should return `DataBackendStatus.AWAY`.
    """

    class MockAsyncIOMotorClientAdmin:
        """Mock the `AsyncIOMotorClient.admin` property."""

        @staticmethod
        async def command(command: str):
            """Mock the `command` method always raising a `ConnectionFailure`."""
            assert command == "ping"
            raise ConnectionFailure("Connection failure")

    class MockAsyncIOMotorClient:
        """Mock the `motor.motor_asyncio.AsyncIOMotorClient`."""

        admin = MockAsyncIOMotorClientAdmin

    backend = async_mongo_backend()
    monkeypatch.setattr(backend, "client", MockAsyncIOMotorClient)
    with caplog.at_level(logging.ERROR):
        assert await backend.status() == DataBackendStatus.AWAY

    assert (
        "ralph.backends.data.async_mongo",
        logging.ERROR,
        "Failed to connect to MongoDB: Connection failure",
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_mongo_status_with_error_status(
    async_mongo_backend, monkeypatch, caplog
):
    """Test the `AsyncMongoDataBackend.status` method, given a failed serverStatus
    command, should return `DataBackendStatus.ERROR`.
    """

    class MockAsyncIOMotorClientAdmin:
        """Mock the `AsyncIOMotorClient.admin` property."""

        @staticmethod
        async def command(command: str):
            """Mock the `command` method always raising a `ConnectionFailure`."""
            if command == "ping":
                return
            assert command == "serverStatus"
            raise PyMongoError("Server status failure")

    class MockAsyncIOMotorClient:
        """Mock the `motor.motor_asyncio.AsyncIOMotorClient`."""

        admin = MockAsyncIOMotorClientAdmin

    backend = async_mongo_backend()
    monkeypatch.setattr(backend, "client", MockAsyncIOMotorClient)
    with caplog.at_level(logging.ERROR):
        assert await backend.status() == DataBackendStatus.ERROR

    assert (
        "ralph.backends.data.async_mongo",
        logging.ERROR,
        "Failed to get MongoDB server status: Server status failure",
    ) in caplog.record_tuples

    # Given a MongoDB serverStatus query returning an ok status different from 1,
    # the `status` method should return `DataBackendStatus.ERROR`.

    class MockAsyncIOMotorClientAdmin:
        """Mock the `AsyncIOMotorClient.admin` property."""

        @staticmethod
        async def command(*_, **__):
            """Mock the `command` method always raising a `ConnectionFailure`."""
            return {"ok": 0}

    class MockAsyncIOMotorClient:
        """Mock the `motor.motor_asyncio.AsyncIOMotorClient`."""

        admin = MockAsyncIOMotorClientAdmin

    monkeypatch.setattr(backend, "client", MockAsyncIOMotorClient)

    with caplog.at_level(logging.ERROR):
        assert await backend.status() == DataBackendStatus.ERROR

    assert (
        "ralph.backends.data.async_mongo",
        logging.ERROR,
        "MongoDB `serverStatus` command did not return 1.0",
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_mongo_status_with_ok_status(
    async_mongo_backend, monkeypatch
):
    """Test the `AsyncMongoDataBackend.status` method, given a successful connection
    and serverStatus command, should return `DataBackendStatus.OK`.
    """

    class MockAsyncIOMotorClientAdmin:
        """Mock the `AsyncIOMotorClient.admin` property."""

        @staticmethod
        async def command(command: str):
            """Mock the `command` method always ensuring the server is up."""
            return {"ok": 1.0}

    class MockAsyncIOMotorClient:
        """Mock the `motor.motor_asyncio.AsyncIOMotorClient`."""

        admin = MockAsyncIOMotorClientAdmin

    backend = async_mongo_backend()
    monkeypatch.setattr(backend, "client", MockAsyncIOMotorClient)

    assert await backend.status() == DataBackendStatus.OK


@pytest.mark.parametrize("invalid_character", [" ", ".", "/", '"'])
@pytest.mark.anyio
async def test_backends_data_async_mongo_list_with_invalid_target(
    invalid_character, async_mongo_backend, caplog
):
    """Test the `AsyncMongoDataBackend.list` method given an invalid `target` argument,
    should raise a `BackendParameterException`.
    """
    backend = async_mongo_backend()
    msg = (
        f"The target=`foo{invalid_character}bar` is not a valid database name: "
        f"database names cannot contain the character '{invalid_character}'"
    )

    with pytest.raises(BackendParameterException, match=msg):
        with caplog.at_level(logging.ERROR):
            async for result in backend.list(f"foo{invalid_character}bar"):
                next(result)

    assert (
        "ralph.backends.data.async_mongo",
        logging.ERROR,
        msg,
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_mongo_list_with_failure(
    async_mongo_backend, monkeypatch, caplog
):
    """Test the `AsyncMongoDataBackend.list` method given a failure while retrieving
    MongoDB collections, should raise a `BackendException`.
    """

    def mock_list_collections():
        """Mock the `list_collections` method always raising an exception."""
        raise PyMongoError("Connection error")

    backend = async_mongo_backend()
    monkeypatch.setattr(backend.database, "list_collections", mock_list_collections)
    msg = "Failed to list MongoDB collections: Connection error"
    with pytest.raises(BackendException, match=msg):
        with caplog.at_level(logging.ERROR):
            async for result in backend.list():
                next(result)

    assert (
        "ralph.backends.data.async_mongo",
        logging.ERROR,
        msg,
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_mongo_list_without_history(
    mongo, async_mongo_backend, monkeypatch
):
    """Test the `AsyncMongoDataBackend.list` method without history."""

    backend = async_mongo_backend()

    # Test `list` method with default parameters
    result = [collection async for collection in backend.list()]
    assert result == [MONGO_TEST_COLLECTION]

    # Test `list` method with a given target (database for MongoDB)
    result = [
        collection async for collection in backend.list(target=MONGO_TEST_DATABASE)
    ]
    assert result == [MONGO_TEST_COLLECTION]

    # Test `list` method with detailed information about collections
    result = [collection async for collection in backend.list(details=True)]
    assert result[0]["name"] == MONGO_TEST_COLLECTION

    # Test `list` method with several collections
    await backend.database.create_collection("bar")
    await backend.database.create_collection("baz")

    result = [collection async for collection in backend.list()]
    assert sorted(result) == sorted([MONGO_TEST_COLLECTION, "bar", "baz"])

    result = [collection["name"] async for collection in backend.list(details=True)]
    assert sorted(result) == (sorted([MONGO_TEST_COLLECTION, "bar", "baz"]))

    result = [collection async for collection in backend.list("non_existent_database")]
    assert not result


@pytest.mark.anyio
async def test_backends_data_async_mongo_list_with_history(
    mongo, async_mongo_backend, caplog
):
    """Test the `AsyncMongoDataBackend.list` method given `new` argument set to
    `True`, should log a warning message.
    """
    backend = async_mongo_backend()
    with caplog.at_level(logging.WARNING):
        result = [
            collection
            async for collection in backend.list("non_existent_database", new=True)
        ]
        assert not list(result)

    assert (
        "ralph.backends.data.async_mongo",
        logging.WARNING,
        "The `new` argument is ignored",
    ) in caplog.record_tuples


@pytest.mark.anyio
@pytest.mark.parametrize("prefetch", [1, 10])
async def test_backends_data_async_mongo_read_with_raw_output(
    prefetch, mongo, async_mongo_backend
):
    """Test the `AsyncMongoDataBackend.read` method with `raw_output` set to `True`."""

    backend = async_mongo_backend()
    documents = [
        {"_id": ObjectId("64945e53a4ee2699573e0d6f"), "id": "foo"},
        {"_id": ObjectId("64945e530468d817b1f756da"), "id": "bar"},
        {"_id": ObjectId("64945e530468d817b1f756db"), "id": "baz"},
    ]
    expected = [
        b'{"_id": "64945e53a4ee2699573e0d6f", "id": "foo"}\n',
        b'{"_id": "64945e530468d817b1f756da", "id": "bar"}\n',
        b'{"_id": "64945e530468d817b1f756db", "id": "baz"}\n',
    ]
    await backend.collection.insert_many(documents)
    await backend.database.foobar.insert_many(documents[:2])

    result = [
        statement
        async for statement in backend.read(raw_output=True, prefetch=prefetch)
    ]
    assert result == expected
    result = [
        statement async for statement in backend.read(raw_output=True, target="foobar")
    ]
    assert result == expected[:2]
    result = [
        statement async for statement in backend.read(raw_output=True, chunk_size=2)
    ]
    assert result == expected
    result = [
        statement async for statement in backend.read(raw_output=True, chunk_size=1000)
    ]
    assert result == expected


@pytest.mark.anyio
@pytest.mark.parametrize("prefetch", [1, 10])
async def test_backends_data_async_mongo_read_without_raw_output(
    prefetch, mongo, async_mongo_backend
):
    """Test the `AsyncMongoDataBackend.read` method with `raw_output` set to
    `False`.
    """

    backend = async_mongo_backend()
    documents = [
        {"_id": ObjectId("64945e53a4ee2699573e0d6f"), "id": "foo"},
        {"_id": ObjectId("64945e530468d817b1f756da"), "id": "bar"},
        {"_id": ObjectId("64945e530468d817b1f756db"), "id": "baz"},
    ]
    expected = [
        {"_id": "64945e53a4ee2699573e0d6f", "id": "foo"},
        {"_id": "64945e530468d817b1f756da", "id": "bar"},
        {"_id": "64945e530468d817b1f756db", "id": "baz"},
    ]
    await backend.collection.insert_many(documents)
    await backend.database.foobar.insert_many(documents[:2])

    assert [
        statement async for statement in backend.read(prefetch=prefetch)
    ] == expected
    assert [statement async for statement in backend.read(target="foobar")] == expected[
        :2
    ]
    assert [statement async for statement in backend.read(chunk_size=2)] == expected
    assert [statement async for statement in backend.read(chunk_size=1000)] == expected


@pytest.mark.parametrize(
    "invalid_target,error",
    [
        (".foo", "must not start or end with '.': '.foo'"),
        ("foo.", "must not start or end with '.': 'foo.'"),
        ("foo$bar", "must not contain '$': 'foo$bar'"),
        ("foo..bar", "cannot be empty"),
    ],
)
@pytest.mark.anyio
async def test_backends_data_async_mongo_read_with_invalid_target(
    invalid_target,
    error,
    async_mongo_backend,
    caplog,
):
    """Test the `AsyncMongoDataBackend.read` method given an invalid `target` argument,
    should raise a `BackendParameterException`.
    """
    backend = async_mongo_backend()
    msg = (
        f"The target=`{invalid_target}` is not a valid collection name: "
        f"collection names {error}"
    )
    with pytest.raises(BackendParameterException, match=msg.replace("$", r"\$")):
        with caplog.at_level(logging.ERROR):
            async for statement in backend.read(target=invalid_target):
                next(statement)

    assert (
        "ralph.backends.data.async_mongo",
        logging.ERROR,
        msg,
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_mongo_read_with_failure(
    async_mongo_backend, monkeypatch, caplog
):
    """Test the `AsyncMongoDataBackend.read` method given an AsyncIOMotorClient failure,
    should raise a `BackendException`.
    """

    def mock_find(*_, **__):
        """Mock the `motor.motor_asyncio.AsyncIOMotorClient.collection.find`
        method returning a failing Cursor.
        """
        raise PyMongoError("MongoDB internal failure")

    backend = async_mongo_backend()
    monkeypatch.setattr(backend.collection, "find", mock_find)
    msg = "Failed to execute MongoDB query: MongoDB internal failure"
    with pytest.raises(BackendException, match=msg):
        with caplog.at_level(logging.ERROR):
            result = [statement async for statement in backend.read()]
            next(result)

    assert (
        "ralph.backends.data.async_mongo",
        logging.ERROR,
        msg,
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_mongo_read_with_ignore_errors(
    mongo, async_mongo_backend, caplog
):
    """Test the `AsyncMongoDataBackend.read` method with `ignore_errors` set to `True`,
    given a collection containing unparsable documents, should skip the invalid
    documents.
    """

    backend = async_mongo_backend()
    unparsable_value = ObjectId()
    documents = [
        {"_id": ObjectId("64945e53a4ee2699573e0d6f"), "id": "foo"},
        {"_id": ObjectId("64945e530468d817b1f756da"), "id": unparsable_value},
        {"_id": ObjectId("64945e530468d817b1f756db"), "id": "baz"},
    ]
    expected = [
        b'{"_id": "64945e53a4ee2699573e0d6f", "id": "foo"}\n',
        b'{"_id": "64945e530468d817b1f756db", "id": "baz"}\n',
    ]
    await backend.collection.insert_many(documents)
    await backend.database.foobar.insert_many(documents[:2])
    kwargs = {"raw_output": True, "ignore_errors": True}
    with caplog.at_level(logging.WARNING):
        assert [statement async for statement in backend.read(**kwargs)] == expected
        assert [
            statement async for statement in backend.read(**kwargs, target="foobar")
        ] == expected[:1]
        assert [
            statement async for statement in backend.read(**kwargs, chunk_size=2)
        ] == expected
        assert [
            statement async for statement in backend.read(**kwargs, chunk_size=1000)
        ] == expected

    assert (
        "ralph.backends.data.async_mongo",
        logging.WARNING,
        "Failed to encode JSON: Object of type ObjectId is not "
        "JSON serializable, for document: {'_id': '64945e530468d817b1f756da', "
        f"'id': ObjectId('{unparsable_value}')}}, at line 1",
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_mongo_read_without_ignore_errors(
    mongo, async_mongo_backend, caplog
):
    """Test the `AsyncMongoDataBackend.read` method with `ignore_errors` set to `False`,
    given a collection containing unparsable documents, should raise a
    `BackendException`.
    """

    backend = async_mongo_backend()
    unparsable_value = ObjectId()
    documents = [
        {"_id": ObjectId("64945e53a4ee2699573e0d6f"), "id": "foo"},
        {"_id": ObjectId("64945e530468d817b1f756da"), "id": unparsable_value},
        {"_id": ObjectId("64945e530468d817b1f756db"), "id": "baz"},
    ]
    expected = b'{"_id": "64945e53a4ee2699573e0d6f", "id": "foo"}'
    await backend.collection.insert_many(documents)
    await backend.database.foobar.insert_many(documents[:2])
    kwargs = {"raw_output": True, "ignore_errors": False}
    msg = (
        "Failed to encode JSON: Object of type ObjectId is not JSON serializable, "
        "for document: {'_id': '64945e530468d817b1f756da', "
        f"'id': ObjectId('{unparsable_value}')}}, at line 1"
    )
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=re.escape(msg)):
            result = [statement async for statement in backend.read(**kwargs)]
            assert next(result) == expected
            next(result)
        with pytest.raises(BackendException, match=re.escape(msg)):
            result = [
                statement async for statement in backend.read(**kwargs, target="foobar")
            ]
            assert next(result) == expected
            next(result)
        with pytest.raises(BackendException, match=re.escape(msg)):
            result = [
                statement async for statement in backend.read(**kwargs, chunk_size=2)
            ]
            assert next(result) == expected
            next(result)
        with pytest.raises(BackendException, match=re.escape(msg)):
            result = [
                statement async for statement in backend.read(**kwargs, chunk_size=1000)
            ]
            assert next(result) == expected
            next(result)

    assert (
        "ralph.backends.data.async_mongo",
        logging.ERROR,
        msg,
    ) in caplog.record_tuples


@pytest.mark.parametrize(
    "query",
    [
        '{"filter": {"id": {"$eq": "bar"}}, "projection": {"id": 1}}',
        {"filter": {"id": {"$eq": "bar"}}, "projection": {"id": 1}},
        MongoQuery(
            query_string='{"filter": {"id": {"$eq": "bar"}}, "projection": {"id": 1}}'
        ),
        # Given both `query_string` and other query arguments, only the `query_string`
        # should be applied.
        MongoQuery(
            query_string='{"filter": {"id": {"$eq": "bar"}}, "projection": {"id": 1}}',
            filter={"id": {"$eq": "foo"}},
            projection={"id": 0},
        ),
        MongoQuery(filter={"id": {"$eq": "bar"}}, projection={"id": 1}),
    ],
)
@pytest.mark.anyio
async def test_backends_data_async_mongo_read_with_query(
    query, mongo, async_mongo_backend
):
    """Test the `AsyncMongoDataBackend.read` method given a query argument."""

    # Create records
    backend = async_mongo_backend()
    documents = [
        {"_id": ObjectId("64945e53a4ee2699573e0d6f"), "id": "foo", "qux": "foo"},
        {"_id": ObjectId("64945e530468d817b1f756da"), "id": "bar", "qux": "foo"},
        {"_id": ObjectId("64945e530468d817b1f756db"), "id": "bar", "qux": "foo"},
    ]
    expected = [
        {"_id": "64945e530468d817b1f756da", "id": "bar"},
        {"_id": "64945e530468d817b1f756db", "id": "bar"},
    ]
    await backend.collection.insert_many(documents)

    assert [statement async for statement in backend.read(query=query)] == expected
    assert [
        statement async for statement in backend.read(query=query, chunk_size=1)
    ] == expected
    assert [
        statement async for statement in backend.read(query=query, chunk_size=1000)
    ] == expected


@pytest.mark.anyio
async def test_backends_data_async_mongo_write_with_concurrency(
    async_es_backend, monkeypatch
):
    """Test the `AsyncMongoDataBackend.write` method, given `concurrency` set,
    should pass the `concurrency` value to `AsyncWritable.write`.
    """

    async def mock_write(  # noqa: PLR0913
        self, data, target, chunk_size, ignore_errors, operation_type, concurrency
    ):
        """Mock the AsyncWritable `write` method."""
        assert concurrency == 4
        return 3

    backend = async_es_backend()
    monkeypatch.setattr(AsyncWritable, "write", mock_write)
    assert await backend.write([b"bar"], concurrency=4) == 3


@pytest.mark.anyio
async def test_backends_data_async_mongo_write_with_target(
    mongo,
    async_mongo_backend,
):
    """Test the `AsyncMongoDataBackend.write` method, given a valid `target` argument,
    should write documents to the target collection.
    """

    backend = async_mongo_backend()
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    assert await backend.write(documents, target="foo_target_collection") == 2

    # The documents should not be written to the default collection.
    assert not [statement async for statement in backend.read()]

    result = [
        statement async for statement in backend.read(target="foo_target_collection")
    ]
    assert result[0] == {
        "_id": "62b9ce922c26b46b68ffc68f",
        "_source": {"id": "foo", **timestamp},
    }
    assert result[1] == {
        "_id": "62b9ce92fcde2b2edba56bf4",
        "_source": {"id": "bar", **timestamp},
    }


@pytest.mark.anyio
@pytest.mark.parametrize(
    "invalid_target,error",
    [
        (".foo", "must not start or end with '.': '.foo'"),
        ("foo.", "must not start or end with '.': 'foo.'"),
        ("foo$bar", "must not contain '$': 'foo$bar'"),
        ("foo..bar", "cannot be empty"),
    ],
)
async def test_backends_data_async_mongo_write_with_invalid_target(
    invalid_target, error, async_mongo_backend, caplog
):
    """Test the `AsyncMongoDataBackend.write` method given an invalid `target` argument,
    should raise a `BackendParameterException`.
    """
    backend = async_mongo_backend()
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    msg = (
        f"The target=`{invalid_target}` is not a valid collection name: "
        f"collection names {error}"
    )
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendParameterException, match=msg.replace("$", r"\$")):
            await backend.write(documents, target=invalid_target)

    assert (
        "ralph.backends.data.async_mongo",
        logging.ERROR,
        msg,
    ) in caplog.record_tuples
    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_mongo_write_without_target(
    mongo,
    async_mongo_backend,
):
    """Test the `AsyncMongoDataBackend.write` method, given a no `target` argument,
    should write documents to the default collection.
    """

    backend = async_mongo_backend()
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    assert await backend.write(documents) == 2
    result = [statement async for statement in backend.read()]
    assert result[0] == {
        "_id": "62b9ce922c26b46b68ffc68f",
        "_source": {"id": "foo", **timestamp},
    }
    assert result[1] == {
        "_id": "62b9ce92fcde2b2edba56bf4",
        "_source": {"id": "bar", **timestamp},
    }


@pytest.mark.anyio
async def test_backends_data_async_mongo_write_with_duplicated_key_error(
    mongo, async_mongo_backend
):
    """Test the `AsyncMongoDataBackend.write` method, given documents with duplicated
    ids, should write the documents until it encounters a duplicated id and then raise
    a `BackendException`.
    """

    backend = async_mongo_backend()
    # Identical statement IDs produce the same ObjectIds, leading to a
    # duplicated key write error while trying to bulk import this batch.
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = [
        {"id": "foo", **timestamp},
        {"id": "bar", **timestamp},
        {"id": "bar", **timestamp},
        {"id": "baz", **timestamp},
    ]

    # Given `ignore_errors` argument set to `True`, the `write` method should not raise
    # an exception.
    assert await backend.write(documents, ignore_errors=True) == 2
    assert (
        await backend.write(
            documents, operation_type=BaseOperationType.CREATE, ignore_errors=True
        )
        == 0
    )
    assert [statement async for statement in backend.read()] == [
        {"_id": "62b9ce922c26b46b68ffc68f", "_source": {"id": "foo", **timestamp}},
        {"_id": "62b9ce92fcde2b2edba56bf4", "_source": {"id": "bar", **timestamp}},
    ]

    # Given `ignore_errors` argument set to `False`, the `write` method should raise
    # a `BackendException`.
    with pytest.raises(BackendException, match="E11000 duplicate key error collection"):
        await backend.write(documents)
    with pytest.raises(BackendException, match="E11000 duplicate key error collection"):
        await backend.write(documents, operation_type=BaseOperationType.CREATE)
    assert [statement async for statement in backend.read()] == [
        {"_id": "62b9ce922c26b46b68ffc68f", "_source": {"id": "foo", **timestamp}},
        {"_id": "62b9ce92fcde2b2edba56bf4", "_source": {"id": "bar", **timestamp}},
    ]


@pytest.mark.anyio
async def test_backends_data_async_mongo_write_with_delete_operation(
    mongo, async_mongo_backend
):
    """Test the `AsyncMongoDataBackend.write` method, given a `DELETE` `operation_type`,
    should delete the provided documents from the MongoDB collection.
    """

    backend = async_mongo_backend()
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = [
        {"id": "foo", **timestamp},
        {"id": "bar", **timestamp},
        {"id": "baz", **timestamp},
    ]
    assert await backend.write(documents) == 3
    assert len([statement async for statement in backend.read()]) == 3
    assert (
        await backend.write(documents[:2], operation_type=BaseOperationType.DELETE) == 2
    )
    assert [statement async for statement in backend.read()] == [
        {"_id": "62b9ce92baa5a0964d3320fb", "_source": documents[2]}
    ]

    # Given binary data, the `write` method should have the same behaviour.
    binary_documents = [json.dumps(documents[2]).encode("utf8")]
    assert (
        await backend.write(binary_documents, operation_type=BaseOperationType.DELETE)
        == 1
    )
    assert not [statement async for statement in backend.read()]


@pytest.mark.anyio
async def test_backends_data_async_mongo_write_with_delete_operation_failure(
    mongo, async_mongo_backend, caplog
):
    """Test the `AsyncMongoDataBackend.write` method with the `DELETE` `operation_type`,
    given an AsyncIOMotorClient failure, should raise a `BackendException`.
    """

    backend = async_mongo_backend()
    msg = (
        "Failed to delete document chunk: cannot encode object: <class 'object'>, "
        "of type: <class 'type'>"
    )
    with pytest.raises(BackendException, match=msg):
        await backend.write([{"id": object}], operation_type=BaseOperationType.DELETE)

    # Given `ignore_errors` argument set to `True`, the `write` method should not raise
    # an exception.
    with caplog.at_level(logging.WARNING):
        assert (
            await backend.write(
                [{"id": object}],
                operation_type=BaseOperationType.DELETE,
                ignore_errors=True,
            )
            == 0
        )

    assert (
        "ralph.backends.data.async_mongo",
        logging.WARNING,
        msg,
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_mongo_write_with_update_operation(
    mongo, async_mongo_backend
):
    """Test the `AsyncMongoDataBackend.write` method, given an `UPDATE`
    `operation_type`, should update the provided documents from the MongoDB collection.
    """

    backend = async_mongo_backend()
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]

    assert await backend.write(documents) == 2
    new_timestamp = {"timestamp": "2022-06-27T16:36:50"}
    documents = [{"id": "foo", **new_timestamp}, {"id": "bar", **new_timestamp}]
    assert await backend.write(documents, operation_type=BaseOperationType.UPDATE) == 2

    results = [statement async for statement in backend.read()]
    assert results[0] == {
        "_id": "62b9ce922c26b46b68ffc68f",
        "_source": {"id": "foo", **new_timestamp},
    }
    assert results[1] == {
        "_id": "62b9ce92fcde2b2edba56bf4",
        "_source": {"id": "bar", **new_timestamp},
    }

    # Given binary data, the `write` method should have the same behaviour.
    binary_documents = [json.dumps({"id": "foo", "new_field": "bar"}).encode("utf8")]
    assert (
        await backend.write(binary_documents, operation_type=BaseOperationType.UPDATE)
        == 1
    )
    results = [statement async for statement in backend.read()]
    assert results[0] == {
        "_id": "62b9ce922c26b46b68ffc68f",
        "_source": {"id": "foo", "new_field": "bar"},
    }


@pytest.mark.anyio
async def test_backends_data_async_mongo_write_with_update_operation_failure(
    mongo, async_mongo_backend
):
    """Test the `AsyncMongoDataBackend.write` method with the `UPDATE` `operation_type`,
    given an AsyncIOMotorClient failure, should raise a `BackendException`.
    """

    backend = async_mongo_backend()
    schema = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_source"],
            "properties": {
                "_source": {
                    "bsonType": "object",
                    "required": ["timestamp"],
                    "description": "must be an object",
                    "properties": {
                        "timestamp": {
                            "bsonType": "string",
                            "description": "must be a string and is required",
                        }
                    },
                }
            },
        }
    }
    await backend.database.command(
        "collMod", backend.collection.name, validator=schema, validationLevel="moderate"
    )
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    assert await backend.write(documents) == 2
    documents = [{"id": "foo", "new": "field", **timestamp}, {"id": "bar"}]

    # Given `ignore_errors` argument set to `True`, the `write` method should not raise
    # an exception.
    assert (
        await backend.write(
            documents, operation_type=BaseOperationType.UPDATE, ignore_errors=True
        )
        == 1
    )
    assert [statement async for statement in backend.read()][0]["_source"][
        "new"
    ] == "field"

    msg = "Failed to update document chunk: batch op errors occurred"
    with pytest.raises(BackendException, match=msg):
        await backend.write(
            documents,
            operation_type=BaseOperationType.UPDATE,
            ignore_errors=False,
        )


@pytest.mark.anyio
async def test_backends_data_async_mongo_write_with_append_operation(
    async_mongo_backend, caplog
):
    """Test the `AsyncMongoDataBackend.write` method, given an `APPEND`
    `operation_type`, should raise a `BackendParameterException`.
    """
    backend = async_mongo_backend()
    msg = "Append operation_type is not allowed"
    with pytest.raises(BackendParameterException, match=msg):
        with caplog.at_level(logging.ERROR):
            await backend.write(data=[], operation_type=BaseOperationType.APPEND)

    assert (
        "ralph.backends.data.async_mongo",
        logging.ERROR,
        msg,
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_mongo_write_with_create_operation(
    mongo, async_mongo_backend
):
    """Test the `AsyncMongoDataBackend.write` method, given an `CREATE`
    `operation_type`, should insert the provided documents to the MongoDB collection.
    """

    backend = async_mongo_backend()
    documents = [
        {"timestamp": "2022-06-27T15:36:50"},
        {"timestamp": "2023-06-27T15:36:50"},
    ]
    assert await backend.write(documents, operation_type=BaseOperationType.CREATE) == 2
    results = [statement async for statement in backend.read()]
    assert results[0]["_source"]["timestamp"] == documents[0]["timestamp"]
    assert results[1]["_source"]["timestamp"] == documents[1]["timestamp"]


@pytest.mark.parametrize(
    "document,error",
    [
        ({}, "statement {} has no 'id' field"),
        ({"id": "1"}, "statement {'id': '1'} has no 'timestamp' field"),
        (
            {"id": "1", "timestamp": ""},
            "statement {'id': '1', 'timestamp': ''} has an invalid 'timestamp' field",
        ),
    ],
)
@pytest.mark.anyio
async def test_backends_data_async_mongo_write_with_invalid_documents(
    document, error, mongo, async_mongo_backend, caplog
):
    """Test the `AsyncMongoDataBackend.write` method, given invalid documents, should
    raise a `BackendException`.
    """

    backend = async_mongo_backend()
    with pytest.raises(BackendException, match=error):
        await backend.write([document])

    # Given binary data, the `write` method should have the same behaviour.
    with pytest.raises(BackendException, match=error):
        await backend.write([json.dumps(document).encode("utf8")])

    # Given `ignore_errors` argument set to `True`, the `write` method should not raise
    # an exception.
    with caplog.at_level(logging.WARNING):
        assert await backend.write([document], ignore_errors=True) == 0

    assert (
        "ralph.backends.data.async_mongo",
        logging.WARNING,
        error,
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_mongo_write_with_unparsable_documents(
    async_mongo_backend, caplog
):
    """Test the `AsyncMongoDataBackend.write` method, given unparsable raw documents,
    should raise a `BackendException`.
    """
    backend = async_mongo_backend()
    msg = (
        "Failed to decode JSON: Expecting value: line 1 column 1 (char 0), "
        "for document: b'not valid JSON!', at line 0"
    )
    msg_regex = msg.replace("(", r"\(").replace(")", r"\)")
    with pytest.raises(BackendException, match=msg_regex):
        await backend.write([b"not valid JSON!"])

    # Given `ignore_errors` argument set to `True`, the `write` method should not raise
    # an exception.
    with caplog.at_level(logging.WARNING):
        assert await backend.write([b"not valid JSON!"], ignore_errors=True) == 0

    assert (
        "ralph.backends.data.async_mongo",
        logging.WARNING,
        msg,
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_mongo_write_with_no_data(
    async_mongo_backend, caplog
):
    """Test the `AsyncMongoDataBackend.write` method, given no documents, should return
    0.
    """
    backend = async_mongo_backend()
    with caplog.at_level(logging.INFO):
        assert await backend.write(data=[]) == 0

    msg = "Data Iterator is empty; skipping write to target"
    assert (
        "ralph.backends.data.async_mongo",
        logging.INFO,
        msg,
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_mongo_write_with_custom_chunk_size(
    mongo, async_mongo_backend, caplog
):
    """Test the `AsyncMongoDataBackend.write` method, given a custom chunk_size, should
    insert the provided documents to target collection by batches of size `chunk_size`.
    """

    backend = async_mongo_backend()
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    new_timestamp = {"timestamp": "2023-06-27T15:36:50"}
    documents = [
        {"id": "foo", **timestamp},
        {"id": "bar", **timestamp},
        {"id": "baz", **timestamp},
    ]
    new_documents = [
        {"id": "foo", **new_timestamp},
        {"id": "bar", **new_timestamp},
        {"id": "baz", **new_timestamp},
    ]
    # Index operation type.
    with caplog.at_level(logging.DEBUG):
        assert await backend.write(documents, chunk_size=2) == 3

    assert (
        "ralph.backends.data.async_mongo",
        logging.INFO,
        f"Inserted {len(documents)} documents with success",
    ) in caplog.record_tuples

    assert (
        "ralph.backends.data.async_mongo",
        logging.INFO,
        f"Inserted {len(documents)} documents with success",
    ) in caplog.record_tuples

    assert [statement async for statement in backend.read()] == [
        {"_id": "62b9ce922c26b46b68ffc68f", "_source": {"id": "foo", **timestamp}},
        {"_id": "62b9ce92fcde2b2edba56bf4", "_source": {"id": "bar", **timestamp}},
        {"_id": "62b9ce92baa5a0964d3320fb", "_source": {"id": "baz", **timestamp}},
    ]
    # Delete operation type.
    assert (
        await backend.write(
            documents, chunk_size=1, operation_type=BaseOperationType.DELETE
        )
        == 3
    )
    assert not [statement async for statement in backend.read()]
    # Create operation type.
    assert (
        await backend.write(
            documents, chunk_size=1, operation_type=BaseOperationType.CREATE
        )
        == 3
    )
    assert [statement async for statement in backend.read()] == [
        {"_id": "62b9ce922c26b46b68ffc68f", "_source": {"id": "foo", **timestamp}},
        {"_id": "62b9ce92fcde2b2edba56bf4", "_source": {"id": "bar", **timestamp}},
        {"_id": "62b9ce92baa5a0964d3320fb", "_source": {"id": "baz", **timestamp}},
    ]
    # Update operation type.
    assert (
        await backend.write(
            new_documents, chunk_size=3, operation_type=BaseOperationType.UPDATE
        )
        == 3
    )
    assert [statement async for statement in backend.read()] == [
        {"_id": "62b9ce922c26b46b68ffc68f", "_source": {"id": "foo", **new_timestamp}},
        {"_id": "62b9ce92fcde2b2edba56bf4", "_source": {"id": "bar", **new_timestamp}},
        {"_id": "62b9ce92baa5a0964d3320fb", "_source": {"id": "baz", **new_timestamp}},
    ]


@pytest.mark.anyio
async def test_backends_data_async_mongo_close_with_failure(
    async_mongo_backend, monkeypatch, caplog
):
    """Test the `AsyncMongoDataBackend.close` method, given a failed close,
    should raise a BackendException.
    """

    class MockAsyncIOMotorClient:
        """Mock the `motor.motor_asyncio.AsyncIOMotorClient`."""

        @staticmethod
        def close():
            """Mock the `close` method always raising a `PyMongoError`."""
            raise PyMongoError("Close failure")

    backend = async_mongo_backend()
    monkeypatch.setattr(backend, "client", MockAsyncIOMotorClient)

    msg = "Failed to close AsyncIOMotorClient: Close failure"
    with pytest.raises(BackendException, match=msg):
        with caplog.at_level(logging.ERROR):
            await backend.close()

    assert (
        "ralph.backends.data.async_mongo",
        logging.ERROR,
        "Failed to close AsyncIOMotorClient: Close failure",
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_mongo_close(async_mongo_backend):
    """Test the `AsyncMongoDataBackend.close` method."""

    backend = async_mongo_backend()

    # Not possible to connect to client after closing it
    await backend.close()
    assert await backend.status() == DataBackendStatus.AWAY
