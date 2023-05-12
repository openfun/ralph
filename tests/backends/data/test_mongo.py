# pylint: disable=too-many-lines
"""Tests for Ralph mongo data backend."""

import json
import logging
from datetime import datetime

import pytest
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from ralph.backends.data.base import BaseOperationType, DataBackendStatus
from ralph.backends.data.mongo import MongoDataBackend, MongoLRSBackend, MongoQuery
from ralph.backends.lrs.base import StatementParameters
from ralph.exceptions import (
    BackendException,
    BackendParameterException,
    BadFormatException,
)

from tests.fixtures.backends import (
    MONGO_TEST_COLLECTION,
    MONGO_TEST_CONNECTION_URI,
    MONGO_TEST_DATABASE,
    MONGO_TEST_FORWARDING_COLLECTION,
)


def test_backends_data_mongo_data_backend_instantiation_with_settings():
    """Test the Mongo backend instantiation."""
    assert MongoDataBackend.name == "mongo"
    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)

    assert isinstance(backend.client, MongoClient)
    assert hasattr(backend.client, MONGO_TEST_DATABASE)
    database = getattr(backend.client, MONGO_TEST_DATABASE)
    assert hasattr(database, MONGO_TEST_COLLECTION)


def test_backends_data_mongo_data_backend_read_method_without_raw_output(mongo):
    """Test the mongo backend get method."""
    # Create records
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = MongoDataBackend.to_documents(
        [
            {"id": "foo", **timestamp},
            {"id": "bar", **timestamp},
        ]
    )
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    collection.insert_many(documents)

    # Get backend
    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)
    expected = [
        {"_id": "62b9ce922c26b46b68ffc68f", "_source": {"id": "foo", **timestamp}},
        {"_id": "62b9ce92fcde2b2edba56bf4", "_source": {"id": "bar", **timestamp}},
    ]
    assert list(backend.read()) == expected
    assert list(backend.read(chunk_size=2)) == expected
    assert list(backend.read(chunk_size=1000)) == expected


def test_backends_data_mongo_data_backend_read_method_with_query_string(mongo):
    """Test the mongo backend get method with query string."""
    # Create records
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = MongoDataBackend.to_documents(
        [
            {"id": "foo", **timestamp},
            {"id": "bar", **timestamp},
        ]
    )
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    collection.insert_many(documents)

    # Get backend
    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)
    expected = [
        {"_id": "62b9ce922c26b46b68ffc68f", "_source": {"id": "foo", **timestamp}},
    ]
    query = MongoQuery(
        query_string=json.dumps({"filter": {"_source.id": {"$eq": "foo"}}})
    )
    assert list(backend.read(query=query)) == expected
    assert list(backend.read(query=query, chunk_size=2)) == expected
    assert list(backend.read(query=query, chunk_size=1000)) == expected


def test_backends_data_mongo_data_backend_list_method(mongo):
    """Test the mongo backend list method."""
    # Create records
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = MongoDataBackend.to_documents(
        [
            {"id": "foo", **timestamp},
            {"id": "bar", **timestamp},
        ]
    )
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    collection.insert_many(documents)

    # Get backend
    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)
    assert list(backend.list(details=True))[0]["name"] == MONGO_TEST_COLLECTION
    assert list(backend.list(details=False)) == [MONGO_TEST_COLLECTION]


def test_backends_data_mongo_data_backend_list_method_with_details(mongo):
    """Test the mongo backend list method."""
    # Create records
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = MongoDataBackend.to_documents(
        [
            {"id": "foo", **timestamp},
            {"id": "bar", **timestamp},
        ]
    )
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    collection.insert_many(documents)

    # Get backend
    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)
    assert [elt["_id"] for elt in list(backend.read())] == [
        "62b9ce922c26b46b68ffc68f",
        "62b9ce92fcde2b2edba56bf4",
    ]


def test_backends_data_mongo_data_backend_list_method_with_target(mongo):
    """Test the mongo backend list method."""
    # Create records
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = MongoDataBackend.to_documents(
        [
            {"id": "foo", **timestamp},
            {"id": "bar", **timestamp},
        ]
    )
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    collection.insert_many(documents)

    # Get backend
    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)
    assert [elt["_id"] for elt in list(backend.read(target=MONGO_TEST_COLLECTION))] == [
        "62b9ce922c26b46b68ffc68f",
        "62b9ce92fcde2b2edba56bf4",
    ]


def test_backends_database_mongo_get_method_with_raw_ouput(mongo):
    """Test the mongo backend get method with raw output."""
    # Create records
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = MongoDataBackend.to_documents(
        [
            {"id": "foo", **timestamp},
            {"id": "bar", **timestamp},
        ]
    )
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    collection.insert_many(documents)

    # Get backend
    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)
    expected = [
        {"_id": "62b9ce922c26b46b68ffc68f", "id": "foo", **timestamp},
        {"_id": "62b9ce92fcde2b2edba56bf4", "id": "bar", **timestamp},
    ]
    results = list(backend.read(raw_output=True))
    assert len(results) == 2
    assert isinstance(results[0], bytes)
    assert json.loads(results[0])["_source"]["id"] == expected[0]["id"]


def test_backends_database_mongo_get_method_with_target(mongo):
    """Test the mongo backend get method with raw output."""
    # Create records
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = MongoDataBackend.to_documents(
        [
            {"id": "foo", **timestamp},
            {"id": "bar", **timestamp},
        ]
    )
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    collection.insert_many(documents)

    # Get backend
    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)
    expected = [
        {"_id": "62b9ce922c26b46b68ffc68f", "id": "foo", **timestamp},
        {"_id": "62b9ce92fcde2b2edba56bf4", "id": "bar", **timestamp},
    ]
    results = list(backend.read(raw_output=True, target=MONGO_TEST_COLLECTION))
    assert len(results) == 2
    assert isinstance(results[0], bytes)
    assert json.loads(results[0])["_source"]["id"] == expected[0]["id"]


def test_backends_data_mongo_data_backend_read_method_with_query(mongo):
    """Test the mongo backend get method with a custom query."""
    # Create records
    timestamp = {"timestamp": datetime.now().isoformat()}
    documents = MongoDataBackend.to_documents(
        [
            {"id": "foo", "bool": 1, **timestamp},
            {"id": "bar", "bool": 0, **timestamp},
            {"id": "lol", "bool": 1, **timestamp},
        ]
    )
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    collection.insert_many(documents)

    # Get backend
    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)

    # Test filtering
    query = MongoQuery(filter={"_source.bool": {"$eq": 1}})
    results = list(backend.read(query=query))
    assert len(results) == 2
    assert results[0]["_source"]["id"] == "foo"
    assert results[1]["_source"]["id"] == "lol"

    # Test projection
    query = MongoQuery(projection={"_source.bool": 1})
    results = list(backend.read(query=query))
    assert len(results) == 3
    assert list(results[0]["_source"].keys()) == ["bool"]
    assert list(results[1]["_source"].keys()) == ["bool"]
    assert list(results[2]["_source"].keys()) == ["bool"]

    # Test filtering and projection
    query = MongoQuery(
        filter={"_source.bool": {"$eq": 0}}, projection={"_source.id": 1}
    )
    results = list(backend.read(query=query))
    assert len(results) == 1
    assert results[0]["_source"]["id"] == "bar"
    assert list(results[0]["_source"].keys()) == ["id"]


def test_backends_database_mongo_to_documents_method():
    """Test the mongo backend to_documents method."""
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [
        {"id": "foo", **timestamp},
        {"id": "bar", **timestamp},
        {"id": "bar", **timestamp},
    ]
    documents = MongoDataBackend.to_documents(statements)

    assert next(documents) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", **timestamp},
    }
    assert next(documents) == {
        "_id": ObjectId("62b9ce92fcde2b2edba56bf4"),
        "_source": {"id": "bar", **timestamp},
    }
    # Identical statement ID produces the same ObjectId
    assert next(documents) == {
        "_id": ObjectId("62b9ce92fcde2b2edba56bf4"),
        "_source": {"id": "bar", **timestamp},
    }


def test_backends_database_mongo_to_documents_method_when_statement_has_no_id(caplog):
    """Test the mongo backend to_documents method when a statement has no id field."""
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [{"id": "foo", **timestamp}, timestamp, {"id": "bar", **timestamp}]

    documents = MongoDataBackend.to_documents(statements, ignore_errors=False)
    assert next(documents) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", **timestamp},
    }
    with pytest.raises(
        BadFormatException, match=f"statement {timestamp} has no 'id' field"
    ):
        next(documents)

    documents = MongoDataBackend.to_documents(statements, ignore_errors=True)
    assert next(documents) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", **timestamp},
    }
    assert next(documents) == {
        "_id": ObjectId("62b9ce92fcde2b2edba56bf4"),
        "_source": {"id": "bar", **timestamp},
    }
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"
    assert caplog.records[0].message == f"statement {timestamp} has no 'id' field"


def test_backends_database_mongo_to_documents_method_when_statement_has_no_timestamp(
    caplog,
):
    """Tests the mongo backend to_documents method when a statement has no timestamp."""
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [{"id": "foo", **timestamp}, {"id": "bar"}, {"id": "baz", **timestamp}]

    documents = MongoDataBackend.to_documents(statements, ignore_errors=False)
    assert next(documents) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", **timestamp},
    }

    with pytest.raises(
        BadFormatException, match="statement {'id': 'bar'} has no 'timestamp' field"
    ):
        next(documents)

    documents = MongoDataBackend.to_documents(statements, ignore_errors=True)
    assert next(documents) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", **timestamp},
    }
    assert next(documents) == {
        "_id": ObjectId("62b9ce92baa5a0964d3320fb"),
        "_source": {"id": "baz", **timestamp},
    }
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"
    assert caplog.records[0].message == (
        "statement {'id': 'bar'} has no 'timestamp' field"
    )


def test_backends_database_mongo_to_documents_method_with_invalid_timestamp(caplog):
    """Tests the mongo backend to_documents method given a statement with an invalid
    timestamp.
    """
    valid_timestamp = {"timestamp": "2022-06-27T15:36:50"}
    invalid_timestamp = {"timestamp": "This is not a valid timestamp!"}
    invalid_statement = {"id": "bar", **invalid_timestamp}
    statements = [
        {"id": "foo", **valid_timestamp},
        invalid_statement,
        {"id": "baz", **valid_timestamp},
    ]

    documents = MongoDataBackend.to_documents(statements, ignore_errors=False)
    assert next(documents) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", **valid_timestamp},
    }

    with pytest.raises(
        BadFormatException,
        match=f"statement {invalid_statement} has an invalid 'timestamp' field",
    ):
        next(documents)

    documents = MongoDataBackend.to_documents(statements, ignore_errors=True)
    assert next(documents) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", **valid_timestamp},
    }
    assert next(documents) == {
        "_id": ObjectId("62b9ce92baa5a0964d3320fb"),
        "_source": {"id": "baz", **valid_timestamp},
    }
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"
    assert caplog.records[0].message == (
        f"statement {invalid_statement} has an invalid 'timestamp' field"
    )


def test_backends_database_mongo_bulk_import_method(mongo):
    """Test the mongo backend bulk_import method."""
    # pylint: disable=unused-argument

    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    backend.bulk_import(MongoDataBackend.to_documents(statements))

    results = backend.collection.find()
    assert next(results) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", **timestamp},
    }
    assert next(results) == {
        "_id": ObjectId("62b9ce92fcde2b2edba56bf4"),
        "_source": {"id": "bar", **timestamp},
    }


def test_backends_database_mongo_bulk_delete_method(mongo):
    """Test the mongo backend bulk_delete method."""
    # pylint: disable=unused-argument

    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    backend.bulk_import(MongoDataBackend.to_documents(statements))
    documents = [st["id"] for st in statements]
    backend.bulk_delete(batch=documents)

    results = backend.collection.find()
    assert next(results, None) is None


def test_backends_database_mongo_bulk_update_method(mongo):
    """Test the mongo backend bulk_update method."""
    # pylint: disable=unused-argument

    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    backend.bulk_import(MongoDataBackend.to_documents(statements))
    statements = [
        {"id": "foo", "text": "foo", **timestamp},
        {"id": "bar", "text": "bar", **timestamp},
    ]
    success = backend.write(data=statements, operation_type=BaseOperationType.UPDATE)
    assert success == 2

    results = backend.collection.find()
    assert next(results) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", "text": "foo", **timestamp},
    }
    assert next(results) == {
        "_id": ObjectId("62b9ce92fcde2b2edba56bf4"),
        "_source": {"id": "bar", "text": "bar", **timestamp},
    }


def test_backends_database_mongo_bulk_update_method_iterable(mongo):
    """Test the mongo backend bulk_update method."""
    # pylint: disable=unused-argument

    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    backend.bulk_import(MongoDataBackend.to_documents(statements))
    statements = [
        {"id": "foo", "text": "foo", **timestamp},
        {"id": "bar", "text": "bar", **timestamp},
    ]
    statements = iter(statements)
    success = backend.write(data=statements, operation_type=BaseOperationType.UPDATE)
    assert success == 2
    results = backend.collection.find()
    assert next(results) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", "text": "foo", **timestamp},
    }
    assert next(results) == {
        "_id": ObjectId("62b9ce92fcde2b2edba56bf4"),
        "_source": {"id": "bar", "text": "bar", **timestamp},
    }


def test_backends_database_mongo_bulk_wrong_operation_type(mongo):
    """Test the mongo backend bulk_update method."""
    # pylint: disable=unused-argument

    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    backend.bulk_import(MongoDataBackend.to_documents(statements))
    statements = [
        {"id": "foo", "text": "foo", **timestamp},
        {"id": "bar", "text": "bar", **timestamp},
    ]

    with pytest.raises(
        BackendParameterException,
        match=f"{BaseOperationType.APPEND.name} operation_type is not allowed.",
    ):
        backend.write(data=statements, operation_type=BaseOperationType.APPEND)


def test_backends_database_mongo_bulk_no_data(mongo):
    """Test the mongo backend bulk_update method."""
    # pylint: disable=unused-argument

    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)

    success = backend.write(data=[], operation_type=BaseOperationType.CREATE)

    assert success == 0


def test_backends_database_mongo_bulk_import_method_with_duplicated_key(mongo):
    """Test the mongo backend bulk_import method with a duplicated key conflict."""
    # pylint: disable=unused-argument

    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)

    # Identical statement ID produces the same ObjectId, leading to a
    # duplicated key write error while trying to bulk import this batch
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [
        {"id": "foo", **timestamp},
        {"id": "bar", **timestamp},
        {"id": "bar", **timestamp},
    ]
    documents = list(MongoDataBackend.to_documents(statements))
    with pytest.raises(BackendException, match="E11000 duplicate key error collection"):
        backend.bulk_import(documents)

    success = backend.bulk_import(documents, ignore_errors=True)
    assert success == 0


def test_backends_database_mongo_bulk_import_method_import_partial_chunks_on_error(
    mongo,
):
    """Test the mongo backend bulk_import method imports partial chunks while raising a
    BulkWriteError and ignoring errors.
    """
    # pylint: disable=unused-argument

    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)

    # Identical statement ID produces the same ObjectId, leading to a
    # duplicated key write error while trying to bulk import this batch
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [
        {"id": "foo", **timestamp},
        {"id": "bar", **timestamp},
        {"id": "baz", **timestamp},
        {"id": "bar", **timestamp},
        {"id": "lol", **timestamp},
    ]
    documents = list(MongoDataBackend.to_documents(statements))
    assert backend.bulk_import(documents, ignore_errors=True) == 3


def test_backends_database_mongo_put_method(mongo):
    """Test the mongo backend put method."""
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    assert collection.estimated_document_count() == 0

    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)

    success = backend.write(statements)
    assert success == 2
    assert collection.estimated_document_count() == 2

    results = collection.find()
    assert next(results) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", **timestamp},
    }
    assert next(results) == {
        "_id": ObjectId("62b9ce92fcde2b2edba56bf4"),
        "_source": {"id": "bar", **timestamp},
    }


def test_backends_database_mongo_put_method_bytes(mongo):
    """Test the mongo backend put method with bytes."""
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    assert collection.estimated_document_count() == 0

    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [
        {"id": "foo", "text": "foo", **timestamp},
        {"id": "bar", "text": "bar", **timestamp},
    ]
    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)
    byte_data = []
    for item in statements:
        json_str = json.dumps(item, separators=(",", ":"), ensure_ascii=False)
        byte_data.append(json_str.encode("utf-8"))
    success = backend.write(byte_data)
    assert success == 2
    assert collection.estimated_document_count() == 2

    results = collection.find()
    assert next(results) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", "text": "foo", **timestamp},
    }
    assert next(results) == {
        "_id": ObjectId("62b9ce92fcde2b2edba56bf4"),
        "_source": {"id": "bar", "text": "bar", **timestamp},
    }


def test_backends_database_mongo_put_method_bytes_failed(mongo):
    """Test the mongo backend put method with bytes."""
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    assert collection.estimated_document_count() == 0

    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)
    byte_data = []
    json_str = "failed_json_str"
    byte_data.append(json_str.encode("utf-8"))

    with pytest.raises(json.JSONDecodeError):
        success = backend.write(byte_data)
    assert collection.estimated_document_count() == 0

    success = backend.write(byte_data, ignore_errors=True)
    assert success == 0
    assert collection.estimated_document_count() == 0


def test_backends_database_mongo_put_method_with_target(mongo):
    """Test the mongo backend put method."""
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    assert collection.estimated_document_count() == 0

    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)

    success = backend.write(statements, target=MONGO_TEST_COLLECTION)
    assert success == 2
    assert collection.estimated_document_count() == 2

    results = collection.find()
    assert next(results) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", **timestamp},
    }
    assert next(results) == {
        "_id": ObjectId("62b9ce92fcde2b2edba56bf4"),
        "_source": {"id": "bar", **timestamp},
    }


def test_backends_database_mongo_put_method_with_no_ids(mongo):
    """Test the mongo backend put method with no IDs."""
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    assert collection.estimated_document_count() == 0

    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [{**timestamp}, {**timestamp}]
    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)

    success = backend.write(statements, operation_type=BaseOperationType.INDEX)
    assert success == 2
    assert collection.estimated_document_count() == 2


def test_backends_database_mongo_put_method_with_custom_chunk_size(mongo):
    """Test the mongo backend put method with a custom chunk_size."""
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    assert collection.estimated_document_count() == 0

    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]

    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)
    success = backend.write(statements, chunk_size=2)
    assert success == 2
    assert collection.estimated_document_count() == 2

    results = collection.find()
    assert next(results) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", **timestamp},
    }
    assert next(results) == {
        "_id": ObjectId("62b9ce92fcde2b2edba56bf4"),
        "_source": {"id": "bar", **timestamp},
    }


def test_backends_database_mongo_put_method_with_duplicated_key(mongo):
    """Test the mongo backend put method with a duplicated key conflict."""
    # pylint: disable=unused-argument

    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)

    # Identical statement ID produces the same ObjectId, leading to a
    # duplicated key write error while trying to bulk import this batch
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [
        {"id": "foo", **timestamp},
        {"id": "bar", **timestamp},
        {"id": "bar", **timestamp},
    ]
    with pytest.raises(BackendException, match="E11000 duplicate key error collection"):
        backend.write(statements)

    success = backend.write(statements, ignore_errors=True)
    assert success == 0


def test_backends_data_mongo_data_backend_write_method_with_update_operation(
    mongo,
):
    """Test the mongo backend write method with a update operation."""
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    assert collection.estimated_document_count() == 0

    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)

    success = backend.write(statements)
    assert success == 2
    assert collection.estimated_document_count() == 2

    results = collection.find()
    assert next(results) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", **timestamp},
    }
    assert next(results) == {
        "_id": ObjectId("62b9ce92fcde2b2edba56bf4"),
        "_source": {"id": "bar", **timestamp},
    }

    timestamp = {"timestamp": "2022-06-27T16:36:50"}
    statements = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    success = backend.write(
        statements, chunk_size=2, operation_type=BaseOperationType.UPDATE
    )
    assert success == 2
    assert collection.estimated_document_count() == 2

    results = collection.find()
    assert next(results) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", **timestamp},
    }
    assert next(results) == {
        "_id": ObjectId("62b9ce92fcde2b2edba56bf4"),
        "_source": {"id": "bar", **timestamp},
    }


def test_backends_data_mongo_data_backend_write_method_with_delete_operation(
    mongo,
):
    """Test the mongo backend write method with a delete operation."""
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    assert collection.estimated_document_count() == 0

    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [
        {"id": "foo", **timestamp},
        {"id": "bar", **timestamp},
        {"id": "baz", **timestamp},
    ]
    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)

    success = backend.write(statements, chunk_size=2)
    assert success == 3
    assert collection.estimated_document_count() == 3

    results = collection.find()
    assert next(results) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", **timestamp},
    }
    assert next(results) == {
        "_id": ObjectId("62b9ce92fcde2b2edba56bf4"),
        "_source": {"id": "bar", **timestamp},
    }

    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [
        {"id": "foo", **timestamp},
        {"id": "bar", **timestamp},
        {"id": "baz", **timestamp},
    ]
    success = backend.write(
        statements, chunk_size=2, operation_type=BaseOperationType.DELETE
    )
    assert success == 3

    assert not list(backend.read())

    assert collection.estimated_document_count() == 0


def test_backends_database_mongo_query_statements(monkeypatch, caplog, mongo):
    """Tests the mongo backend query_statements method, given a search query failure,
    should raise a BackendException and log the error.
    """
    # pylint: disable=unused-argument,use-implicit-booleaness-not-comparison

    # Instantiate Mongo Databases

    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoLRSBackend(settings)

    # Insert documents
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    meta = {
        "actor": {"account": {"name": "test_name"}},
        "verb": {"id": "verb_id"},
        "object": {"id": "http://example.com", "objectType": "Activity"},
    }
    collection_document = list(
        MongoDataBackend.to_documents(
            [
                {"id": "62b9ce922c26b46b68ffc68f", **timestamp, **meta},
                {"id": "62b9ce92fcde2b2edba56bf4", **timestamp, **meta},
            ]
        )
    )
    backend.bulk_import(collection_document)

    statement_parameters = StatementParameters()
    statement_parameters.activity = "http://example.com"
    statement_parameters.registration = ObjectId("62b9ce922c26b46b68ffc68f")
    statement_parameters.since = "2020-01-01T00:00:00.000000+00:00"
    statement_parameters.until = "2022-12-01T15:36:50"
    statement_parameters.search_after = ObjectId("62b9ce922c26b46b68ffc68f")
    statement_parameters.limit = 25
    statement_parameters.ascending = True
    statement_parameters.related_activities = True
    statement_parameters.related_agents = True
    statement_parameters.format = "ids"
    statement_parameters.agent = "test_name"
    statement_parameters.verb = "verb_id"
    statement_parameters.attachments = False
    statement_parameters.search_after = ObjectId("62b9ce922c26b46b68ffc68f")
    statement_parameters.statementId = "62b9ce922c26b46b68ffc68f"
    statement_query_result = backend.query_statements(statement_parameters)

    assert len(statement_query_result.statements) > 0


def test_backends_database_mongo_query_statements_with_search_query_failure(
    monkeypatch, caplog, mongo
):
    """Tests the mongo backend query_statements method, given a search query failure,
    should raise a BackendException and log the error.
    """
    # pylint: disable=unused-argument

    def mock_find(**_):
        """Mocks the MongoClient.collection.find method."""
        raise PyMongoError("Something is wrong")

    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoLRSBackend(settings)
    monkeypatch.setattr(backend.collection, "find", mock_find)

    caplog.set_level(logging.ERROR)

    msg = "'Failed to execute MongoDB query', 'Something is wrong'"
    with pytest.raises(BackendException, match=msg):
        backend.query_statements(StatementParameters())

    logger_name = "ralph.backends.data.mongo"
    msg = "Failed to execute MongoDB query. Something is wrong"
    assert caplog.record_tuples == [(logger_name, logging.ERROR, msg)]


def test_backends_database_mongo_query_statements_by_ids_with_search_query_failure(
    monkeypatch, caplog, mongo
):
    """Tests the mongo backend query_statements_by_ids method, given a search query
    failure, should raise a BackendException and log the error.
    """
    # pylint: disable=unused-argument

    def mock_find(**_):
        """Mocks the MongoClient.collection.find method."""
        raise ValueError("Something is wrong")

    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoLRSBackend(settings)
    monkeypatch.setattr(backend.collection, "find", mock_find)
    caplog.set_level(logging.ERROR)

    msg = "'Failed to execute MongoDB query', 'Something is wrong'"
    with pytest.raises(BackendException, match=msg):
        backend.query_statements_by_ids(StatementParameters())

    logger_name = "ralph.backends.data.mongo"
    msg = "Failed to execute MongoDB query. Something is wrong"
    assert caplog.record_tuples == [(logger_name, logging.ERROR, msg)]


def test_backends_database_mongo_query_statements_by_ids_with_multiple_collections(
    mongo, mongo_forwarding
):
    """Tests the mongo backend query_statements_by_ids method, given a valid search
    query, should execute the query uniquely on the specified collection and return the
    expected results.
    """
    # pylint: disable=unused-argument,use-implicit-booleaness-not-comparison

    # Instantiate Mongo Databases

    settings_1 = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend_1 = MongoLRSBackend(settings_1)

    settings_2 = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_FORWARDING_COLLECTION,
    )
    backend_2 = MongoLRSBackend(settings_2)

    # Insert documents
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    collection_1_document = list(
        MongoDataBackend.to_documents([{"id": "1", **timestamp}])
    )
    collection_2_document = list(
        MongoDataBackend.to_documents([{"id": "2", **timestamp}])
    )
    backend_1.bulk_import(collection_1_document)
    backend_2.bulk_import(collection_2_document)

    # Check the expected search query results
    assert backend_1.query_statements_by_ids(["1"]) == collection_1_document
    assert backend_1.query_statements_by_ids(["2"]) == []
    assert backend_2.query_statements_by_ids(["1"]) == []
    assert backend_2.query_statements_by_ids(["2"]) == collection_2_document


def test_backends_database_mongo_status(mongo):
    """Test the Mongo status method.

    As pymongo is monkeypatching the MongoDB client to add admin object, it's
    barely untestable. 😢
    """
    # pylint: disable=unused-argument

    settings = MongoDataBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)
    assert backend.status() == DataBackendStatus.OK


def test_backends_database_mongo_status_connection_failed(mongo):
    """Test the Mongo status method.

    As pymongo is monkeypatching the MongoDB client to add admin object, it's
    barely untestable. 😢
    """
    # pylint: disable=unused-argument

    settings = MongoDataBackend.settings_class(
        CONNECTION_URI="mongodb://localhost:27018",
        DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    backend = MongoDataBackend(settings)
    assert backend.status() == DataBackendStatus.AWAY
