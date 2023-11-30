"""Tests for Ralph MongoDB data backend."""

import json
import logging
import re

import pytest
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

from ralph.backends.data.base import BaseOperationType, DataBackendStatus
from ralph.backends.data.mongo import (
    MongoClientOptions,
    MongoDataBackend,
    MongoDataBackendSettings,
    MongoQuery,
)
from ralph.exceptions import BackendException, BackendParameterException

from tests.fixtures.backends import (
    MONGO_TEST_COLLECTION,
    MONGO_TEST_CONNECTION_URI,
    MONGO_TEST_DATABASE,
)


def test_backends_data_mongo_default_instantiation(monkeypatch, fs):
    """Test the `MongoDataBackend` default instantiation."""

    fs.create_file(".env")
    backend_settings_names = [
        "CONNECTION_URI",
        "DEFAULT_DATABASE",
        "DEFAULT_COLLECTION",
        "CLIENT_OPTIONS",
        "READ_CHUNK_SIZE",
        "LOCALE_ENCODING",
    ]
    for name in backend_settings_names:
        monkeypatch.delenv(f"RALPH_BACKENDS__DATA__MONGO__{name}", raising=False)

    assert MongoDataBackend.name == "mongo"
    assert MongoDataBackend.query_class == MongoQuery
    assert MongoDataBackend.default_operation_type == BaseOperationType.INDEX
    assert MongoDataBackend.settings_class == MongoDataBackendSettings
    backend = MongoDataBackend()
    assert isinstance(backend.client, MongoClient)
    assert backend.database.name == "statements"
    assert backend.collection.name == "marsha"
    assert backend.settings.CONNECTION_URI == "mongodb://localhost:27017/"
    assert backend.settings.CLIENT_OPTIONS == MongoClientOptions()
    assert backend.settings.LOCALE_ENCODING == "utf8"
    assert backend.settings.READ_CHUNK_SIZE == 500
    assert backend.settings.WRITE_CHUNK_SIZE == 500

    # Test overriding default values with environment variables.
    monkeypatch.setenv("RALPH_BACKENDS__DATA__MONGO__CLIENT_OPTIONS__tz_aware", True)
    backend = MongoDataBackend()
    assert backend.settings.CLIENT_OPTIONS == MongoClientOptions(tz_aware=True)
    backend.close()


def test_backends_data_mongo_instantiation_with_settings():
    """Test the `MongoDataBackend` instantiation with settings."""
    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DEFAULT_DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION="foo",
        CLIENT_OPTIONS={"tz_aware": "True"},
        LOCALE_ENCODING="utf8",
        READ_CHUNK_SIZE=1000,
        WRITE_CHUNK_SIZE=999,
    )
    backend = MongoDataBackend(settings)
    assert backend.database.name == MONGO_TEST_DATABASE
    assert backend.collection.name == "foo"
    assert backend.settings.CONNECTION_URI == MONGO_TEST_CONNECTION_URI
    assert backend.settings.CLIENT_OPTIONS == MongoClientOptions(tz_aware=True)
    assert backend.settings.LOCALE_ENCODING == "utf8"
    assert backend.settings.READ_CHUNK_SIZE == 1000
    assert backend.settings.WRITE_CHUNK_SIZE == 999

    try:
        MongoDataBackend(settings)
    except Exception as err:  # noqa: BLE001
        pytest.fail(f"Two MongoDataBackends should not raise exceptions: {err}")
    backend.close()


def test_backends_data_mongo_status_with_connection_failure(
    mongo_backend, monkeypatch, caplog
):
    """Test the `MongoDataBackend.status` method, given a connection failure, should
    return `DataBackendStatus.AWAY`.
    """

    class MockMongoClientAdmin:
        """Mock the `MongoClient.admin` property."""

        @staticmethod
        def command(command: str):
            """Mock the `command` method always raising a `ConnectionFailure`."""
            assert command == "ping"
            raise ConnectionFailure("Connection failure")

    class MockMongoClient:
        """Mock the `pymongo.MongoClient`."""

        admin = MockMongoClientAdmin

    backend = mongo_backend()
    monkeypatch.setattr(backend, "client", MockMongoClient)
    with caplog.at_level(logging.ERROR):
        assert backend.status() == DataBackendStatus.AWAY

    assert (
        "ralph.backends.data.mongo",
        logging.ERROR,
        "Failed to connect to MongoDB: Connection failure",
    ) in caplog.record_tuples


def test_backends_data_mongo_status_with_error_status(
    mongo_backend, monkeypatch, caplog
):
    """Test the `MongoDataBackend.status` method, given a failed serverStatus command,
    should return `DataBackendStatus.ERROR`.
    """

    class MockMongoClientAdmin:
        """Mock the `MongoClient.admin` property."""

        @staticmethod
        def command(command: str):
            """Mock the `command` method always raising a `ConnectionFailure`."""
            if command == "ping":
                return
            assert command == "serverStatus"
            raise PyMongoError("Server status failure")

    class MockMongoClient:
        """Mock the `pymongo.MongoClient`."""

        admin = MockMongoClientAdmin

    backend = mongo_backend()
    monkeypatch.setattr(backend, "client", MockMongoClient)
    with caplog.at_level(logging.ERROR):
        assert backend.status() == DataBackendStatus.ERROR

    assert (
        "ralph.backends.data.mongo",
        logging.ERROR,
        "Failed to get MongoDB server status: Server status failure",
    ) in caplog.record_tuples

    # Given a MongoDB serverStatus query returning an ok status different from 1,
    # the `status` method should return `DataBackendStatus.ERROR`.
    monkeypatch.setattr(MockMongoClientAdmin, "command", lambda x: {"ok": 0})
    with caplog.at_level(logging.ERROR):
        assert backend.status() == DataBackendStatus.ERROR

    assert (
        "ralph.backends.data.mongo",
        logging.ERROR,
        "MongoDB `serverStatus` command did not return 1.0",
    ) in caplog.record_tuples


def test_backends_data_mongo_status_with_ok_status(mongo_backend):
    """Test the `MongoDataBackend.status` method, given a successful connection and
    serverStatus command, should return `DataBackendStatus.OK`.
    """
    backend = mongo_backend()
    assert backend.status() == DataBackendStatus.OK
    backend.close()


@pytest.mark.parametrize("invalid_character", [" ", ".", "/", '"'])
def test_backends_data_mongo_list_with_invalid_target(
    invalid_character, mongo_backend, caplog
):
    """Test the `MongoDataBackend.list` method given an invalid `target` argument,
    should raise a `BackendParameterException`.
    """
    backend = mongo_backend()
    msg = (
        f"The target=`foo{invalid_character}bar` is not a valid database name: "
        f"database names cannot contain the character '{invalid_character}'"
    )
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendParameterException, match=msg):
            list(backend.list(f"foo{invalid_character}bar"))

    assert ("ralph.backends.data.mongo", logging.ERROR, msg) in caplog.record_tuples
    backend.close()


def test_backends_data_mongo_list_with_failure(mongo_backend, monkeypatch, caplog):
    """Test the `MongoDataBackend.list` method given a failure while retrieving MongoDB
    collections, should raise a `BackendException`.
    """

    def list_collections():
        """Mock the `list_collections` method always raising an exception."""
        raise PyMongoError("Connection error")

    backend = mongo_backend()
    monkeypatch.setattr(backend.database, "list_collections", list_collections)
    msg = "Failed to list MongoDB collections: Connection error"
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=msg):
            list(backend.list())

    assert ("ralph.backends.data.mongo", logging.ERROR, msg) in caplog.record_tuples
    backend.close()


def test_backends_data_mongo_list_without_history(mongo, mongo_backend):
    """Test the `MongoDataBackend.list` method without history."""

    backend = mongo_backend()
    assert list(backend.list()) == [MONGO_TEST_COLLECTION]
    assert list(backend.list(MONGO_TEST_DATABASE)) == [MONGO_TEST_COLLECTION]
    assert list(backend.list(details=True))[0]["name"] == MONGO_TEST_COLLECTION
    backend.database.create_collection("bar")
    backend.database.create_collection("baz")
    assert sorted(backend.list()) == sorted([MONGO_TEST_COLLECTION, "bar", "baz"])
    assert sorted(collection["name"] for collection in backend.list(details=True)) == (
        sorted([MONGO_TEST_COLLECTION, "bar", "baz"])
    )
    assert not list(backend.list("non_existent_database"))
    backend.close()


def test_backends_data_mongo_list_with_history(mongo_backend, caplog):
    """Test the `MongoDataBackend.list` method given `new` argument set to `True`,
    should log a warning message.
    """
    backend = mongo_backend()
    with caplog.at_level(logging.WARNING):
        assert not list(backend.list("non_existent_database", new=True))

    assert (
        "ralph.backends.data.mongo",
        logging.WARNING,
        "The `new` argument is ignored",
    ) in caplog.record_tuples
    backend.close()


def test_backends_data_mongo_read_with_raw_output(mongo, mongo_backend):
    """Test the `MongoDataBackend.read` method with `raw_output` set to `True`."""

    backend = mongo_backend()
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
    backend.collection.insert_many(documents)
    backend.database.foobar.insert_many(documents[:2])
    assert list(backend.read(raw_output=True)) == expected
    assert list(backend.read(raw_output=True, target="foobar")) == expected[:2]
    assert list(backend.read(raw_output=True, chunk_size=2)) == expected
    assert list(backend.read(raw_output=True, chunk_size=1000)) == expected
    backend.close()


def test_backends_data_mongo_read_without_raw_output(mongo, mongo_backend):
    """Test the `MongoDataBackend.read` method with `raw_output` set to `False`."""

    backend = mongo_backend()
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
    backend.collection.insert_many(documents)
    backend.database.foobar.insert_many(documents[:2])
    assert list(backend.read()) == expected
    assert list(backend.read(target="foobar")) == expected[:2]
    assert list(backend.read(chunk_size=2)) == expected
    assert list(backend.read(chunk_size=1000)) == expected
    backend.close()


@pytest.mark.parametrize(
    "invalid_target,error",
    [
        (".foo", "must not start or end with '.': '.foo'"),
        ("foo.", "must not start or end with '.': 'foo.'"),
        ("foo$bar", "must not contain '$': 'foo$bar'"),
        ("foo..bar", "cannot be empty"),
    ],
)
def test_backends_data_mongo_read_with_invalid_target(
    invalid_target, error, mongo_backend, caplog
):
    """Test the `MongoDataBackend.read` method given an invalid `target` argument,
    should raise a `BackendParameterException`.
    """
    backend = mongo_backend()
    msg = (
        f"The target=`{invalid_target}` is not a valid collection name: "
        f"collection names {error}"
    )
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendParameterException, match=msg.replace("$", r"\$")):
            list(backend.read(target=invalid_target))

    assert ("ralph.backends.data.mongo", logging.ERROR, msg) in caplog.record_tuples
    backend.close()


def test_backends_data_mongo_read_with_failure(mongo_backend, monkeypatch, caplog):
    """Test the `MongoDataBackend.read` method given a MongoClient failure,
    should raise a `BackendException`.
    """

    def mock_find(batch_size, query=None):
        """Mock the `MongoClient.collection.find` method always raising an Exception."""
        assert batch_size == 500
        assert not query
        raise PyMongoError("MongoDB internal failure")

    backend = mongo_backend()
    monkeypatch.setattr(backend.collection, "find", mock_find)
    msg = "Failed to execute MongoDB query: MongoDB internal failure"
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=msg):
            list(backend.read())

    assert ("ralph.backends.data.mongo", logging.ERROR, msg) in caplog.record_tuples
    backend.close()


def test_backends_data_mongo_read_with_ignore_errors(mongo, mongo_backend, caplog):
    """Test the `MongoDataBackend.read` method with `ignore_errors` set to `True`, given
    a collection containing unparsable documents, should skip the invalid documents.
    """

    backend = mongo_backend()
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
    backend.collection.insert_many(documents)
    backend.database.foobar.insert_many(documents[:2])
    kwargs = {"raw_output": True, "ignore_errors": True}
    with caplog.at_level(logging.WARNING):
        assert list(backend.read(**kwargs)) == expected
        assert list(backend.read(**kwargs, target="foobar")) == expected[:1]
        assert list(backend.read(**kwargs, chunk_size=2)) == expected
        assert list(backend.read(**kwargs, chunk_size=1000)) == expected

    assert (
        "ralph.utils",
        logging.WARNING,
        "Failed to encode JSON: Object of type ObjectId is not "
        "JSON serializable, for document: {'_id': '64945e530468d817b1f756da', "
        f"'id': ObjectId('{unparsable_value}')}}, at line 1",
    ) in caplog.record_tuples
    backend.close()


def test_backends_data_mongo_read_without_ignore_errors(mongo, mongo_backend, caplog):
    """Test the `MongoDataBackend.read` method with `ignore_errors` set to `False`,
    given a collection containing unparsable documents, should raise a
    `BackendException`.
    """

    backend = mongo_backend()
    unparsable_value = ObjectId()
    documents = [
        {"_id": ObjectId("64945e53a4ee2699573e0d6f"), "id": "foo"},
        {"_id": ObjectId("64945e530468d817b1f756da"), "id": unparsable_value},
        {"_id": ObjectId("64945e530468d817b1f756db"), "id": "baz"},
    ]
    expected = b'{"_id": "64945e53a4ee2699573e0d6f", "id": "foo"}\n'
    backend.collection.insert_many(documents)
    backend.database.foobar.insert_many(documents[:2])
    kwargs = {"raw_output": True, "ignore_errors": False}
    msg = (
        "Failed to encode JSON: Object of type ObjectId is not "
        "JSON serializable, for document: {'_id': '64945e530468d817b1f756da', "
        f"'id': ObjectId('{unparsable_value}')}}, at line 1"
    )
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=re.escape(msg)):
            result = backend.read(**kwargs)
            assert next(result) == expected
            next(result)
        with pytest.raises(BackendException, match=re.escape(msg)):
            result = backend.read(**kwargs, target="foobar")
            assert next(result) == expected
            next(result)
        with pytest.raises(BackendException, match=re.escape(msg)):
            result = backend.read(**kwargs, chunk_size=2)
            assert next(result) == expected
            next(result)
        with pytest.raises(BackendException, match=re.escape(msg)):
            result = backend.read(**kwargs, chunk_size=1000)
            assert next(result) == expected
            next(result)

    error_log = ("ralph.utils", logging.ERROR, msg)
    assert len(list(filter(lambda x: x == error_log, caplog.record_tuples))) == 4
    backend.close()


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
def test_backends_data_mongo_read_with_query(query, mongo, mongo_backend):
    """Test the `MongoDataBackend.read` method given a query argument."""

    # Create records
    backend = mongo_backend()
    documents = [
        {"_id": ObjectId("64945e53a4ee2699573e0d6f"), "id": "foo", "qux": "foo"},
        {"_id": ObjectId("64945e530468d817b1f756da"), "id": "bar", "qux": "foo"},
        {"_id": ObjectId("64945e530468d817b1f756db"), "id": "bar", "qux": "foo"},
    ]
    expected = [
        {"_id": "64945e530468d817b1f756da", "id": "bar"},
        {"_id": "64945e530468d817b1f756db", "id": "bar"},
    ]
    backend.collection.insert_many(documents)
    assert list(backend.read(query=query)) == expected
    assert list(backend.read(query=query, chunk_size=1)) == expected
    assert list(backend.read(query=query, chunk_size=1000)) == expected
    backend.close()


def test_backends_data_mongo_write_with_target(mongo, mongo_backend):
    """Test the `MongoDataBackend.write` method, given a valid `target` argument, should
    write documents to the target collection.
    """

    backend = mongo_backend()
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    assert backend.write(documents, target="foo_target_collection") == 2

    # The documents should not be written to the default collection.
    assert not list(backend.read())

    results = backend.read(target="foo_target_collection")
    assert next(results) == {
        "_id": "62b9ce922c26b46b68ffc68f",
        "_source": {"id": "foo", **timestamp},
    }
    assert next(results) == {
        "_id": "62b9ce92fcde2b2edba56bf4",
        "_source": {"id": "bar", **timestamp},
    }
    backend.close()


@pytest.mark.parametrize(
    "invalid_target,error",
    [
        (".foo", "must not start or end with '.': '.foo'"),
        ("foo.", "must not start or end with '.': 'foo.'"),
        ("foo$bar", "must not contain '$': 'foo$bar'"),
        ("foo..bar", "cannot be empty"),
    ],
)
def test_backends_data_mongo_write_with_invalid_target(
    invalid_target, error, mongo_backend, caplog
):
    """Test the `MongoDataBackend.write` method given an invalid `target` argument,
    should raise a `BackendParameterException`.
    """
    backend = mongo_backend()
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    msg = (
        f"The target=`{invalid_target}` is not a valid collection name: "
        f"collection names {error}"
    )
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendParameterException, match=msg.replace("$", r"\$")):
            backend.write(documents, target=invalid_target)

    assert ("ralph.backends.data.mongo", logging.ERROR, msg) in caplog.record_tuples
    backend.close()


def test_backends_data_mongo_write_without_target(mongo, mongo_backend):
    """Test the `MongoDataBackend.write` method, given a no `target` argument, should
    write documents to the default collection.
    """

    backend = mongo_backend()
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    assert backend.write(documents) == 2
    results = backend.read()
    assert next(results) == {
        "_id": "62b9ce922c26b46b68ffc68f",
        "_source": {"id": "foo", **timestamp},
    }
    assert next(results) == {
        "_id": "62b9ce92fcde2b2edba56bf4",
        "_source": {"id": "bar", **timestamp},
    }
    backend.close()


def test_backends_data_mongo_write_with_duplicated_key_error(
    mongo, mongo_backend, caplog
):
    """Test the `MongoDataBackend.write` method, given documents with duplicated ids,
    should write the documents until it encounters a duplicated id and then raise a
    `BackendException`.
    """

    backend = mongo_backend()
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
    assert backend.write(documents, ignore_errors=True) == 2
    assert (
        backend.write(
            documents, operation_type=BaseOperationType.CREATE, ignore_errors=True
        )
        == 0
    )
    assert list(backend.read()) == [
        {"_id": "62b9ce922c26b46b68ffc68f", "_source": {"id": "foo", **timestamp}},
        {"_id": "62b9ce92fcde2b2edba56bf4", "_source": {"id": "bar", **timestamp}},
    ]

    # Given `ignore_errors` argument set to `False`, the `write` method should raise
    # a `BackendException`.
    msg = "E11000 duplicate key error collection"
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=msg):
            backend.write(documents)
        with pytest.raises(BackendException, match=msg) as exception_info:
            backend.write(documents, operation_type=BaseOperationType.CREATE)
        assert list(backend.read()) == [
            {"_id": "62b9ce922c26b46b68ffc68f", "_source": {"id": "foo", **timestamp}},
            {"_id": "62b9ce92fcde2b2edba56bf4", "_source": {"id": "bar", **timestamp}},
        ]

    assert (
        "ralph.backends.data.mongo",
        logging.ERROR,
        exception_info.value.args[0],
    ) in caplog.record_tuples
    backend.close()


def test_backends_data_mongo_write_with_delete_operation(mongo, mongo_backend):
    """Test the `MongoDataBackend.write` method, given a `DELETE` `operation_type`,
    should delete the provided documents from the MongoDB collection.
    """

    backend = mongo_backend()
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = [
        {"id": "foo", **timestamp},
        {"id": "bar", **timestamp},
        {"id": "baz", **timestamp},
    ]
    assert backend.write(documents) == 3
    assert len(list(backend.read())) == 3
    assert backend.write(documents[:2], operation_type=BaseOperationType.DELETE) == 2
    assert list(backend.read()) == [
        {"_id": "62b9ce92baa5a0964d3320fb", "_source": documents[2]}
    ]

    # Given binary data, the `write` method should have the same behaviour.
    binary_documents = [json.dumps(documents[2]).encode("utf8")]
    assert backend.write(binary_documents, operation_type=BaseOperationType.DELETE) == 1
    assert not list(backend.read())
    backend.close()


def test_backends_data_mongo_write_with_delete_operation_failure(
    mongo, mongo_backend, caplog
):
    """Test the `MongoDataBackend.write` method with the `DELETE` `operation_type`,
    given a MongoClient failure, should raise a `BackendException`.
    """

    backend = mongo_backend()
    msg = (
        "Failed to delete document chunk: cannot encode object: <class 'object'>, "
        "of type: <class 'type'>"
    )
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=msg):
            backend.write([{"id": object}], operation_type=BaseOperationType.DELETE)

    assert ("ralph.backends.data.mongo", logging.ERROR, msg) in caplog.record_tuples

    # Given `ignore_errors` argument set to `True`, the `write` method should not raise
    # an exception.
    with caplog.at_level(logging.WARNING):
        assert (
            backend.write(
                [{"id": object}],
                operation_type=BaseOperationType.DELETE,
                ignore_errors=True,
            )
            == 0
        )

    assert ("ralph.backends.data.mongo", logging.WARNING, msg) in caplog.record_tuples
    backend.close()


def test_backends_data_mongo_write_with_update_operation(mongo, mongo_backend):
    """Test the `MongoDataBackend.write` method, given an `UPDATE` `operation_type`,
    should update the provided documents from the MongoDB collection.
    """

    backend = mongo_backend()
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]

    assert backend.write(documents) == 2
    new_timestamp = {"timestamp": "2022-06-27T16:36:50"}
    documents = [{"id": "foo", **new_timestamp}, {"id": "bar", **new_timestamp}]
    assert backend.write(documents, operation_type=BaseOperationType.UPDATE) == 2

    results = backend.read()
    assert next(results) == {
        "_id": "62b9ce922c26b46b68ffc68f",
        "_source": {"id": "foo", **new_timestamp},
    }
    assert next(results) == {
        "_id": "62b9ce92fcde2b2edba56bf4",
        "_source": {"id": "bar", **new_timestamp},
    }

    # Given binary data, the `write` method should have the same behaviour.
    binary_documents = [json.dumps({"id": "foo", "new_field": "bar"}).encode("utf8")]
    assert backend.write(binary_documents, operation_type=BaseOperationType.UPDATE) == 1
    results = backend.read()
    assert next(results) == {
        "_id": "62b9ce922c26b46b68ffc68f",
        "_source": {"id": "foo", "new_field": "bar"},
    }
    backend.close()


def test_backends_data_mongo_write_with_update_operation_failure(
    mongo, mongo_backend, caplog
):
    """Test the `MongoDataBackend.write` method with the `UPDATE` `operation_type`,
    given a MongoClient failure, should raise a `BackendException`.
    """

    backend = mongo_backend()
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
    backend.database.command(
        "collMod", backend.collection.name, validator=schema, validationLevel="moderate"
    )
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    assert backend.write(documents) == 2
    documents = [{"id": "foo", "new": "field", **timestamp}, {"id": "bar"}]

    # Given `ignore_errors` argument set to `True`, the `write` method should not raise
    # an exception.
    assert (
        backend.write(
            documents, operation_type=BaseOperationType.UPDATE, ignore_errors=True
        )
        == 1
    )
    assert next(backend.read())["_source"]["new"] == "field"

    msg = "Failed to update document chunk: batch op errors occurred"
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=msg) as exception_info:
            backend.write(documents, operation_type=BaseOperationType.UPDATE)

    assert (
        "ralph.backends.data.mongo",
        logging.ERROR,
        exception_info.value.args[0],
    ) in caplog.record_tuples
    backend.close()


def test_backends_data_mongo_write_with_append_operation(mongo_backend, caplog):
    """Test the `MongoDataBackend.write` method, given an `APPEND` `operation_type`,
    should raise a `BackendParameterException`.
    """
    backend = mongo_backend()
    msg = "Append operation_type is not allowed"
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendParameterException, match=msg):
            backend.write(data=[], operation_type=BaseOperationType.APPEND)

    assert ("ralph.backends.data.base", logging.ERROR, msg) in caplog.record_tuples
    backend.close()


def test_backends_data_mongo_write_with_create_operation(mongo, mongo_backend):
    """Test the `MongoDataBackend.write` method, given an `CREATE` `operation_type`,
    should insert the provided documents to the MongoDB collection.
    """

    backend = mongo_backend()
    documents = [
        {"timestamp": "2022-06-27T15:36:50"},
        {"timestamp": "2023-06-27T15:36:50"},
    ]
    assert backend.write(documents, operation_type=BaseOperationType.CREATE) == 2
    results = backend.read()
    assert next(results)["_source"]["timestamp"] == documents[0]["timestamp"]
    assert next(results)["_source"]["timestamp"] == documents[1]["timestamp"]
    backend.close()


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
def test_backends_data_mongo_write_with_invalid_documents(
    document, error, mongo, mongo_backend, caplog
):
    """Test the `MongoDataBackend.write` method, given invalid documents, should raise a
    `BackendException`.
    """

    backend = mongo_backend()
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=error):
            backend.write([document])

    # Given binary data, the `write` method should have the same behaviour.
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=error):
            backend.write([json.dumps(document).encode("utf8")])

    # Given `ignore_errors` argument set to `True`, the `write` method should not raise
    # an exception.
    with caplog.at_level(logging.WARNING):
        assert backend.write([document], ignore_errors=True) == 0

    assert ("ralph.backends.data.mongo", logging.WARNING, error) in caplog.record_tuples
    backend.close()


def test_backends_data_mongo_write_with_unparsable_documents(mongo_backend, caplog):
    """Test the `MongoDataBackend.write` method, given unparsable raw documents, should
    raise a `BackendException`.
    """
    backend = mongo_backend()
    msg = (
        "Failed to decode JSON: Expecting value: line 1 column 1 (char 0), "
        "for document: b'not valid JSON!', at line 0"
    )
    msg_regex = msg.replace("(", r"\(").replace(")", r"\)")
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=msg_regex):
            backend.write([b"not valid JSON!"])

    # Given `ignore_errors` argument set to `True`, the `write` method should not raise
    # an exception.
    with caplog.at_level(logging.WARNING):
        assert backend.write([b"not valid JSON!"], ignore_errors=True) == 0

    assert ("ralph.utils", logging.WARNING, msg) in caplog.record_tuples
    backend.close()


def test_backends_data_mongo_write_with_no_data(mongo_backend, caplog):
    """Test the `MongoDataBackend.write` method, given no documents, should return 0."""
    backend = mongo_backend()
    with caplog.at_level(logging.INFO):
        assert backend.write(data=[]) == 0

    msg = "Data Iterator is empty; skipping write to target"
    assert ("ralph.backends.data.base", logging.INFO, msg) in caplog.record_tuples
    backend.close()


def test_backends_data_mongo_write_with_custom_chunk_size(mongo, mongo_backend):
    """Test the `MongoDataBackend.write` method, given a custom chunk_size, should
    insert the provided documents to target collection by batches of size `chunk_size`.
    """

    backend = mongo_backend()
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
    assert backend.write(documents, chunk_size=2) == 3
    assert list(backend.read()) == [
        {"_id": "62b9ce922c26b46b68ffc68f", "_source": {"id": "foo", **timestamp}},
        {"_id": "62b9ce92fcde2b2edba56bf4", "_source": {"id": "bar", **timestamp}},
        {"_id": "62b9ce92baa5a0964d3320fb", "_source": {"id": "baz", **timestamp}},
    ]
    # Delete operation type.
    assert (
        backend.write(documents, chunk_size=1, operation_type=BaseOperationType.DELETE)
        == 3
    )
    assert not list(backend.read())
    # Create operation type.
    assert (
        backend.write(documents, chunk_size=1, operation_type=BaseOperationType.CREATE)
        == 3
    )
    assert list(backend.read()) == [
        {"_id": "62b9ce922c26b46b68ffc68f", "_source": {"id": "foo", **timestamp}},
        {"_id": "62b9ce92fcde2b2edba56bf4", "_source": {"id": "bar", **timestamp}},
        {"_id": "62b9ce92baa5a0964d3320fb", "_source": {"id": "baz", **timestamp}},
    ]
    # Update operation type.
    assert (
        backend.write(
            new_documents, chunk_size=3, operation_type=BaseOperationType.UPDATE
        )
        == 3
    )
    assert list(backend.read()) == [
        {"_id": "62b9ce922c26b46b68ffc68f", "_source": {"id": "foo", **new_timestamp}},
        {"_id": "62b9ce92fcde2b2edba56bf4", "_source": {"id": "bar", **new_timestamp}},
        {"_id": "62b9ce92baa5a0964d3320fb", "_source": {"id": "baz", **new_timestamp}},
    ]
    backend.close()


def test_backends_data_mongo_close_with_failure(mongo_backend, monkeypatch):
    """Test the `MongoDataBackend.close` method."""

    backend = mongo_backend()

    def mock_connection_error():
        """Mongo client close mock that raises a connection error."""
        raise PyMongoError("", (Exception("Mocked connection error"),))

    monkeypatch.setattr(backend.client, "close", mock_connection_error)

    with pytest.raises(BackendException, match="Failed to close MongoDB client"):
        backend.close()


def test_backends_data_mongo_close(mongo_backend):
    """Test the `MongoDataBackend.close` method."""

    backend = mongo_backend()

    # Still possible to connect to client after closing it, as it creates
    # a new connection
    backend.close()
    assert backend.status() == DataBackendStatus.AWAY
