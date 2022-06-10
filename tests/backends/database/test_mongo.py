"""Tests for Ralph mongo database backend"""

import pytest
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

from ralph.backends.database.mongo import MongoDatabase, MongoQuery
from ralph.exceptions import BackendParameterException, BadFormatException

from tests.fixtures.backends import (
    MONGO_TEST_COLLECTION,
    MONGO_TEST_DATABASE,
    MONGO_TEST_URI,
)


def test_backends_database_mongo_database_instantiation():
    """Test the Mongo backend instantiation."""

    assert MongoDatabase.name == "mongo"

    backend = MongoDatabase(
        connection_uri=MONGO_TEST_URI,
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
    documents = MongoDatabase.to_documents([{"id": "foo"}, {"id": "bar"}])
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    collection.insert_many(documents)

    # Get backend
    backend = MongoDatabase(
        connection_uri=MONGO_TEST_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )
    expected = [
        {"_id": "2c26b46b68ffc68ff99b453c", "_source": {"id": "foo"}},
        {"_id": "fcde2b2edba56bf408601fb7", "_source": {"id": "bar"}},
    ]
    assert list(backend.get()) == expected
    assert list(backend.get(chunk_size=1)) == expected
    assert list(backend.get(chunk_size=1000)) == expected


def test_backends_database_mongo_get_method_with_a_custom_query(mongo):
    """Test the mongo backend get method with a custom query."""

    # Create records
    documents = MongoDatabase.to_documents(
        [{"id": "foo", "bool": 1}, {"id": "bar", "bool": 0}, {"id": "lol", "bool": 1}]
    )
    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    collection.insert_many(documents)

    # Get backend
    backend = MongoDatabase(
        connection_uri=MONGO_TEST_URI,
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

    statements = [{"id": "foo"}, {"id": "bar"}, {"id": "bar"}]
    documents = MongoDatabase.to_documents(statements)

    assert next(documents) == {
        "_id": ObjectId("2c26b46b68ffc68ff99b453c"),
        "_source": {"id": "foo"},
    }
    assert next(documents) == {
        "_id": ObjectId("fcde2b2edba56bf408601fb7"),
        "_source": {"id": "bar"},
    }
    # Identical statement ID produces the same ObjectId
    assert next(documents) == {
        "_id": ObjectId("fcde2b2edba56bf408601fb7"),
        "_source": {"id": "bar"},
    }


def test_backends_database_mongo_to_documents_method_when_statement_has_no_id(caplog):
    """Test the mongo backend to_documents method when a statement has no id field."""

    statements = [{"id": "foo"}, {}, {"id": "bar"}]

    documents = MongoDatabase.to_documents(statements, ignore_errors=False)
    assert next(documents) == {
        "_id": ObjectId("2c26b46b68ffc68ff99b453c"),
        "_source": {"id": "foo"},
    }
    with pytest.raises(BadFormatException, match="statement {} has no 'id' field"):
        next(documents)

    documents = MongoDatabase.to_documents(statements, ignore_errors=True)
    assert next(documents) == {
        "_id": ObjectId("2c26b46b68ffc68ff99b453c"),
        "_source": {"id": "foo"},
    }
    assert next(documents) == {
        "_id": ObjectId("fcde2b2edba56bf408601fb7"),
        "_source": {"id": "bar"},
    }
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"
    assert caplog.records[0].message == "statement {} has no 'id' field"


def test_backends_database_mongo_bulk_import_method(mongo):
    """Test the mongo backend bulk_import method."""
    # pylint: disable=unused-argument

    backend = MongoDatabase(
        connection_uri=MONGO_TEST_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )
    statements = [{"id": "foo"}, {"id": "bar"}]
    backend.bulk_import(MongoDatabase.to_documents(statements))

    results = backend.collection.find()
    assert next(results) == {
        "_id": ObjectId("2c26b46b68ffc68ff99b453c"),
        "_source": {"id": "foo"},
    }
    assert next(results) == {
        "_id": ObjectId("fcde2b2edba56bf408601fb7"),
        "_source": {"id": "bar"},
    }


def test_backends_database_mongo_bulk_import_method_with_duplicated_key(mongo):
    """Test the mongo backend bulk_import method with a duplicated key conflict."""
    # pylint: disable=unused-argument

    backend = MongoDatabase(
        connection_uri=MONGO_TEST_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )

    # Identical statement ID produces the same ObjectId, leading to a
    # duplicated key write error while trying to bulk import this batch
    statements = [{"id": "foo"}, {"id": "bar"}, {"id": "bar"}]
    documents = list(MongoDatabase.to_documents(statements))
    with pytest.raises(BulkWriteError, match="E11000 duplicate key error collection"):
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
        connection_uri=MONGO_TEST_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )

    # Identical statement ID produces the same ObjectId, leading to a
    # duplicated key write error while trying to bulk import this batch
    statements = [
        {"id": "foo"},
        {"id": "bar"},
        {"id": "baz"},
        {"id": "bar"},
        {"id": "lol"},
    ]
    documents = list(MongoDatabase.to_documents(statements))
    assert backend.bulk_import(documents, ignore_errors=True) == 3


def test_backends_database_mongo_put_method(mongo):
    """Test the mongo backend put method."""

    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    assert collection.estimated_document_count() == 0

    statements = [{"id": "foo"}, {"id": "bar"}]
    backend = MongoDatabase(
        connection_uri=MONGO_TEST_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )

    success = backend.put(statements)
    assert success == 2
    assert collection.estimated_document_count() == 2

    results = collection.find()
    assert next(results) == {
        "_id": ObjectId("2c26b46b68ffc68ff99b453c"),
        "_source": {"id": "foo"},
    }
    assert next(results) == {
        "_id": ObjectId("fcde2b2edba56bf408601fb7"),
        "_source": {"id": "bar"},
    }


def test_backends_database_mongo_put_method_with_custom_chunk_size(mongo):
    """Test the mongo backend put method with a custom chunk_size."""

    database = getattr(mongo, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    assert collection.estimated_document_count() == 0

    statements = [{"id": "foo"}, {"id": "bar"}]
    backend = MongoDatabase(
        connection_uri=MONGO_TEST_URI,
        database=MONGO_TEST_DATABASE,
        collection=MONGO_TEST_COLLECTION,
    )

    success = backend.put(statements, chunk_size=1)
    assert success == 2
    assert collection.estimated_document_count() == 2

    results = collection.find()
    assert next(results) == {
        "_id": ObjectId("2c26b46b68ffc68ff99b453c"),
        "_source": {"id": "foo"},
    }
    assert next(results) == {
        "_id": ObjectId("fcde2b2edba56bf408601fb7"),
        "_source": {"id": "bar"},
    }
