"""Tests for Ralph mongo database backend."""

import logging
from datetime import datetime

import pytest
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from ralph.backends.database.base import DatabaseStatus, RalphStatementsQuery
from ralph.backends.database.mongo import MongoDatabase, MongoQuery
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


def test_backends_database_mongo_database_instantiation():
    """Test the Mongo backend instantiation."""
    assert MongoDatabase.name == "mongo"

    backend = MongoDatabase(
        connection_uri=MONGO_TEST_CONNECTION_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )

    assert isinstance(backend.client, MongoClient)
    assert hasattr(backend.client, MONGO_TEST_DATABASE)
    database = getattr(backend.client, MONGO_TEST_DATABASE)
    assert hasattr(database, MONGO_TEST_COLLECTION)


def test_backends_database_mongo_get_method(mongo):
    """Test the mongo backend get method."""
    # Create records
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    documents = MongoDatabase.to_documents(
        [
            {"id": "foo", **timestamp},
            {"id": "bar", **timestamp},
        ]
    )
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    collection.insert_many(documents)

    # Get backend
    backend = MongoDatabase(
        connection_uri=MONGO_TEST_CONNECTION_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )
    expected = [
        {"_id": "62b9ce922c26b46b68ffc68f", "_source": {"id": "foo", **timestamp}},
        {"_id": "62b9ce92fcde2b2edba56bf4", "_source": {"id": "bar", **timestamp}},
    ]
    assert list(backend.get()) == expected
    assert list(backend.get(chunk_size=1)) == expected
    assert list(backend.get(chunk_size=1000)) == expected


def test_backends_database_mongo_get_method_with_a_custom_query(mongo):
    """Test the mongo backend get method with a custom query."""
    # Create records
    timestamp = {"timestamp": datetime.now().isoformat()}
    documents = MongoDatabase.to_documents(
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
    backend = MongoDatabase(
        connection_uri=MONGO_TEST_CONNECTION_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )

    # Test filtering
    query = MongoQuery(filter={"_source.bool": {"$eq": 1}})
    results = list(backend.get(query=query))
    assert len(results) == 2
    assert results[0]["_source"]["id"] == "foo"
    assert results[1]["_source"]["id"] == "lol"

    # Test projection
    query = MongoQuery(projection={"_source.bool": 1})
    results = list(backend.get(query=query))
    assert len(results) == 3
    assert list(results[0]["_source"].keys()) == ["bool"]
    assert list(results[1]["_source"].keys()) == ["bool"]
    assert list(results[2]["_source"].keys()) == ["bool"]

    # Test filtering and projection
    query = MongoQuery(
        filter={"_source.bool": {"$eq": 0}}, projection={"_source.id": 1}
    )
    results = list(backend.get(query=query))
    assert len(results) == 1
    assert results[0]["_source"]["id"] == "bar"
    assert list(results[0]["_source"].keys()) == ["id"]

    # Check query argument type
    with pytest.raises(
        BackendParameterException,
        match="'query' argument is expected to be a MongoQuery instance.",
    ):
        list(backend.get(query="foo"))


def test_backends_database_mongo_to_documents_method():
    """Test the mongo backend to_documents method."""
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [
        {"id": "foo", **timestamp},
        {"id": "bar", **timestamp},
        {"id": "bar", **timestamp},
    ]
    documents = MongoDatabase.to_documents(statements)

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

    documents = MongoDatabase.to_documents(statements, ignore_errors=False)
    assert next(documents) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", **timestamp},
    }
    with pytest.raises(
        BadFormatException, match=f"statement {timestamp} has no 'id' field"
    ):
        next(documents)

    documents = MongoDatabase.to_documents(statements, ignore_errors=True)
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

    documents = MongoDatabase.to_documents(statements, ignore_errors=False)
    assert next(documents) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", **timestamp},
    }

    with pytest.raises(
        BadFormatException, match="statement {'id': 'bar'} has no 'timestamp' field"
    ):
        next(documents)

    documents = MongoDatabase.to_documents(statements, ignore_errors=True)
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

    documents = MongoDatabase.to_documents(statements, ignore_errors=False)
    assert next(documents) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", **valid_timestamp},
    }

    with pytest.raises(
        BadFormatException,
        match=f"statement {invalid_statement} has an invalid 'timestamp' field",
    ):
        next(documents)

    documents = MongoDatabase.to_documents(statements, ignore_errors=True)
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

    backend = MongoDatabase(
        connection_uri=MONGO_TEST_CONNECTION_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    backend.bulk_import(MongoDatabase.to_documents(statements))

    results = backend.collection.find()
    assert next(results) == {
        "_id": ObjectId("62b9ce922c26b46b68ffc68f"),
        "_source": {"id": "foo", **timestamp},
    }
    assert next(results) == {
        "_id": ObjectId("62b9ce92fcde2b2edba56bf4"),
        "_source": {"id": "bar", **timestamp},
    }


def test_backends_database_mongo_bulk_import_method_with_duplicated_key(mongo):
    """Test the mongo backend bulk_import method with a duplicated key conflict."""
    # pylint: disable=unused-argument

    backend = MongoDatabase(
        connection_uri=MONGO_TEST_CONNECTION_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )

    # Identical statement ID produces the same ObjectId, leading to a
    # duplicated key write error while trying to bulk import this batch
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [
        {"id": "foo", **timestamp},
        {"id": "bar", **timestamp},
        {"id": "bar", **timestamp},
    ]
    documents = list(MongoDatabase.to_documents(statements))
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

    backend = MongoDatabase(
        connection_uri=MONGO_TEST_CONNECTION_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )

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
    documents = list(MongoDatabase.to_documents(statements))
    assert backend.bulk_import(documents, ignore_errors=True) == 3


def test_backends_database_mongo_put_method(mongo):
    """Test the mongo backend put method."""
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    assert collection.estimated_document_count() == 0

    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    backend = MongoDatabase(
        connection_uri=MONGO_TEST_CONNECTION_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )

    success = backend.put(statements)
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


def test_backends_database_mongo_put_method_with_custom_chunk_size(mongo):
    """Test the mongo backend put method with a custom chunk_size."""
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    assert collection.estimated_document_count() == 0

    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statements = [{"id": "foo", **timestamp}, {"id": "bar", **timestamp}]
    backend = MongoDatabase(
        connection_uri=MONGO_TEST_CONNECTION_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )

    success = backend.put(statements, chunk_size=1)
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

    backend = MongoDatabase(
        connection_uri=MONGO_TEST_CONNECTION_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )
    monkeypatch.setattr(backend.collection, "find", mock_find)

    caplog.set_level(logging.ERROR)

    msg = "'Failed to execute MongoDB query', 'Something is wrong'"
    with pytest.raises(BackendException, match=msg):
        backend.query_statements(RalphStatementsQuery.construct())

    logger_name = "ralph.backends.database.mongo"
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

    backend = MongoDatabase(
        connection_uri=MONGO_TEST_CONNECTION_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )
    monkeypatch.setattr(backend.collection, "find", mock_find)
    caplog.set_level(logging.ERROR)

    msg = "'Failed to execute MongoDB query', 'Something is wrong'"
    with pytest.raises(BackendException, match=msg):
        backend.query_statements_by_ids(RalphStatementsQuery())

    logger_name = "ralph.backends.database.mongo"
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
    backend_1 = MongoDatabase(
        connection_uri=MONGO_TEST_CONNECTION_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )
    backend_2 = MongoDatabase(
        connection_uri=MONGO_TEST_CONNECTION_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_FORWARDING_COLLECTION,
    )

    # Insert documents
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    statement_1 = {"id": "1", **timestamp}
    statement_1_expected = [{"_id": "1", "_source": statement_1}]
    statement_2 = {"id": "2", **timestamp}
    statement_2_expected = [{"_id": "2", "_source": statement_2}]
    collection_1_document = list(MongoDatabase.to_documents([statement_1]))
    collection_2_document = list(MongoDatabase.to_documents([statement_2]))
    backend_1.bulk_import(collection_1_document)
    backend_2.bulk_import(collection_2_document)

    # Check the expected search query results
    assert backend_1.query_statements_by_ids(["1"]) == statement_1_expected
    assert backend_2.query_statements_by_ids(["1"]) == []
    assert backend_2.query_statements_by_ids(["2"]) == statement_2_expected
    assert backend_1.query_statements_by_ids(["2"]) == []


def test_backends_database_mongo_status(mongo):
    """Test the Mongo status method.

    As pymongo is monkeypatching the MongoDB client to add admin object, it's
    barely untestable. 😢
    """
    # pylint: disable=unused-argument

    database = MongoDatabase(
        connection_uri=MONGO_TEST_CONNECTION_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )
    assert database.status() == DatabaseStatus.OK
