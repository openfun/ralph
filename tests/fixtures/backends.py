"""Test fixtures for backends"""

import os
from enum import Enum

import pytest
from elasticsearch import Elasticsearch

# Elasticsearch backend defaults
ES_TEST_INDEX = os.environ.get("RALPH_ES_TEST_INDEX", "test-index")
ES_TEST_HOSTS = os.environ.get("RALPH_ES_TEST_HOSTS", "http://localhost:9200").split(
    ","
)


class NamedClassA:
    """An example named class"""

    name = "A"


class NamedClassB:
    """A second example named class"""

    name = "B"


class NamedClassEnum(Enum):
    """A named test classes Enum"""

    A = "tests.fixtures.backends.NamedClassA"
    B = "tests.fixtures.backends.NamedClassB"


@pytest.fixture
def es():
    """Create / delete an ElasticSearch test index and yield an instanciated client"""
    # pylint: disable=invalid-name

    client = Elasticsearch(ES_TEST_HOSTS)
    client.indices.create(index=ES_TEST_INDEX, ignore=400)
    yield client
    client.indices.delete(index=ES_TEST_INDEX)
