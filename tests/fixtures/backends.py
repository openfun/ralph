"""Test fixtures for backends"""

import os
from enum import Enum

import pytest
from elasticsearch import Elasticsearch

from ralph.backends.storage.swift import SwiftStorage

# Elasticsearch backend defaults
ES_TEST_INDEX = os.environ.get("RALPH_ES_TEST_INDEX", "test-index")
ES_TEST_HOSTS = os.environ.get("RALPH_ES_TEST_HOSTS", "http://localhost:9200").split(
    ","
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


@pytest.fixture
def es():
    """Creates / deletes an ElasticSearch test index and yields an instantiated client."""
    # pylint: disable=invalid-name

    client = Elasticsearch(ES_TEST_HOSTS)
    client.indices.create(index=ES_TEST_INDEX)
    yield client
    client.indices.delete(index=ES_TEST_INDEX)


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
