"""Test fixtures for backends"""

import os
from enum import Enum

import pytest
from elasticsearch import Elasticsearch

from ralph.backends.storage.swift import SwiftStorage

# Elasticsearch backend defaults
ES_TEST_INDEX = os.environ.get("RALPH_ES_TEST_INDEX", "test-index-foo")
ES_TEST_INDEX_TEMPLATE = os.environ.get("RALPH_ES_TEST_INDEX_TEMPLATE", "test-index")
ES_TEST_INDEX_PATTERN = os.environ.get("RALPH_ES_TEST_INDEX_PATTERN", "test-index-*")
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
def es_data_stream():
    """Creates / deletes an ElasticSearch test datastream and yields an instantiated client."""

    client = Elasticsearch(ES_TEST_HOSTS)

    # Create statements index template with enabled data stream
    index_template = {
        "index_patterns": [ES_TEST_INDEX_PATTERN],
        "data_stream": {},
        "template": {
            "mappings": {
                "dynamic": True,
                "dynamic_date_formats": [
                    "strict_date_optional_time",
                    "yyyy/MM/dd HH:mm:ss Z||yyyy/MM/dd Z",
                ],
                "dynamic_templates": [],
                "date_detection": True,
                "numeric_detection": True,
            },
            "settings": {
                "index": {
                    "number_of_shards": "1",
                    "number_of_replicas": "1",
                }
            },
        },
    }
    client.transport.perform_request(
        "PUT", f"/_index_template/{ES_TEST_INDEX_TEMPLATE}", body=index_template
    )

    # Create a datastream matching the index template
    client.indices.create_data_stream(ES_TEST_INDEX)

    yield client

    client.indices.delete_data_stream(ES_TEST_INDEX)
    client.transport.perform_request(
        "DELETE", f"/_index_template/{ES_TEST_INDEX_TEMPLATE}"
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