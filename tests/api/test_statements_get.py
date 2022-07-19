"""Tests for the GET statements endpoint of the Ralph API"""

import re
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import pytest
from elasticsearch import Elasticsearch
from elasticsearch.client import IndicesClient
from elasticsearch.helpers import bulk
from fastapi.testclient import TestClient

from ralph.api import app

from tests.fixtures.backends import ES_TEST_HOSTS

ES_TEST_INDEX = "statements"
ES_CLIENT = Elasticsearch(ES_TEST_HOSTS)
ES_INDICES_CLIENT = IndicesClient(ES_CLIENT)

client = TestClient(app)


def setup_es_index(statements):
    """
    Set up the Elasticsearch index with a bunch of example documents to run tests.
    """
    ES_INDICES_CLIENT.create(index=ES_TEST_INDEX)
    bulk(
        ES_CLIENT,
        [
            {
                "_index": ES_TEST_INDEX,
                "_id": statement["id"],
                "_op_type": "index",
                "_source": statement,
            }
            for statement in statements
        ],
    )
    ES_INDICES_CLIENT.refresh()


@pytest.fixture(autouse=True)
def teardown_es_index():
    """
    Clean up Elasticsearch after each test.
    """
    yield
    ES_INDICES_CLIENT.delete(index=ES_TEST_INDEX)


def test_get_statements(auth_credentials):
    """
    Get statements without any filters set up.
    """
    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
        },
    ]
    setup_es_index(statements)

    response = client.get(
        "/xAPI/statements/", headers={"Authorization": f"Basic {auth_credentials}"}
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1], statements[0]]}


def test_get_statements_ascending(auth_credentials):
    """
    Get statements without any filters set up, with a query parameter to
    order them by ascending timestamp.
    """
    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
        },
    ]
    setup_es_index(statements)

    response = client.get(
        "/xAPI/statements/?ascending=true",
        headers={"Authorization": f"Basic {auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0], statements[1]]}


def test_get_statements_by_statement_id(auth_credentials):
    """
    Filter statements by statement id. Still return a list format response
    to avoid having a polymorphic response type.
    """
    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
        },
    ]
    setup_es_index(statements)

    response = client.get(
        f"/xAPI/statements/?statementId={statements[1]['id']}",
        headers={"Authorization": f"Basic {auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


def test_get_statements_by_agent(auth_credentials):
    """
    Filter statements by agent.
    """
    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": datetime.now().isoformat(),
            "actor": {"account": {"name": "96d61e6c-9cdb-4926-9cff-d3a15c662999"}},
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
            "actor": {"account": {"name": "cdcb1c95-dd5b-4085-8236-9c1580051155"}},
        },
    ]
    setup_es_index(statements)

    response = client.get(
        "/xAPI/statements/?agent=96d61e6c-9cdb-4926-9cff-d3a15c662999",
        headers={"Authorization": f"Basic {auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}


def test_get_statements_by_verb(auth_credentials):
    """
    Filter statements by verb.
    """
    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": datetime.now().isoformat(),
            "verb": {"id": "http://adlnet.gov/expapi/verbs/experienced"},
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
            "verb": {"id": "http://adlnet.gov/expapi/verbs/played"},
        },
    ]
    setup_es_index(statements)

    response = client.get(
        "/xAPI/statements/?verb=" + quote_plus("http://adlnet.gov/expapi/verbs/played"),
        headers={"Authorization": f"Basic {auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


def test_get_statements_by_activity(auth_credentials):
    """
    Filter statements by activity.
    """
    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": datetime.now().isoformat(),
            "object": {
                "id": "58d8bede-155f-48b1-b1ff-a41eb28c2f0b",
                "objectType": "Activity",
            },
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
            "object": {
                "id": "a2956991-200b-40a7-9548-293cdcc06c4b",
                "objectType": "Activity",
            },
        },
    ]
    setup_es_index(statements)

    response = client.get(
        "/xAPI/statements/?activity=a2956991-200b-40a7-9548-293cdcc06c4b",
        headers={"Authorization": f"Basic {auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


def test_get_statements_since_timestamp(auth_credentials):
    """
    Get statements filter by timestamp "since" (or "after") a given timestamp.
    """
    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
        },
    ]
    setup_es_index(statements)

    since = (datetime.now() - timedelta(minutes=30)).isoformat()
    response = client.get(
        f"/xAPI/statements/?since={since}",
        headers={"Authorization": f"Basic {auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


def test_get_statements_until_timestamp(auth_credentials):
    """
    Get statements filter by timestamp "until" (or "before") a given timestamp.
    """
    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
        },
    ]
    setup_es_index(statements)

    until = (datetime.now() - timedelta(minutes=30)).isoformat()
    response = client.get(
        f"/xAPI/statements/?until={until}",
        headers={"Authorization": f"Basic {auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}


def test_get_statements_with_pagination(monkeypatch, auth_credentials):
    """
    When the first page does not contain all possible results, it includes
    a "more" property with a link to get the next page of results.
    """

    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.RUNSERVER_MAX_SEARCH_HITS_COUNT", 2
    )

    statements = [
        {
            "id": "5d345b99-517c-4b54-848e-45010904b177",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
        },
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
        },
    ]
    setup_es_index(statements)

    # First response gets the first two results, with a "more" entry as
    # we have more results to return on a later page.
    first_response = client.get(
        "/xAPI/statements/", headers={"Authorization": f"Basic {auth_credentials}"}
    )
    assert first_response.status_code == 200
    assert first_response.json()["statements"] == [statements[2], statements[1]]
    more_regex = re.compile(r"^/xAPI/statements/\?pit_id=.*&search_after=.*$")
    assert more_regex.match(first_response.json()["more"])

    # Second response gets the missing result from the first response.
    second_response = client.get(
        first_response.json()["more"],
        headers={"Authorization": f"Basic {auth_credentials}"},
    )
    assert second_response.status_code == 200
    assert second_response.json() == {"statements": [statements[0]]}
