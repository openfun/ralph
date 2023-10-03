"""Tests for the GET statements endpoint of the Ralph API."""

import json
from datetime import datetime, timedelta
from urllib.parse import parse_qs, quote_plus, urlparse

import pytest
import responses
from elasticsearch.helpers import bulk
from fastapi.testclient import TestClient

from ralph.api import app
from ralph.api.auth import get_authenticated_user
from ralph.api.auth.basic import get_authenticated_user as get_basic_user
from ralph.api.auth.oidc import get_authenticated_user as get_oidc_user
from ralph.backends.database.clickhouse import ClickHouseDatabase
from ralph.backends.database.mongo import MongoDatabase
from ralph.exceptions import BackendException

from tests.fixtures.backends import (
    CLICKHOUSE_TEST_DATABASE,
    CLICKHOUSE_TEST_HOST,
    CLICKHOUSE_TEST_PORT,
    CLICKHOUSE_TEST_TABLE_NAME,
    ES_TEST_INDEX,
    MONGO_TEST_COLLECTION,
    MONGO_TEST_DATABASE,
    get_clickhouse_test_backend,
    get_es_test_backend,
    get_mongo_test_backend,
)

from ..fixtures.auth import create_mock_basic_auth_user, create_mock_oidc_user
from ..helpers import create_mock_activity, create_mock_agent

client = TestClient(app)


def insert_es_statements(es_client, statements):
    """Insert a bunch of example statements into Elasticsearch for testing."""
    bulk(
        es_client,
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
    es_client.indices.refresh()


def insert_mongo_statements(mongo_client, statements):
    """Insert a bunch of example statements into MongoDB for testing."""
    database = getattr(mongo_client, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    collection.insert_many(list(MongoDatabase.to_documents(statements)))


def insert_clickhouse_statements(statements):
    """Insert a bunch of example statements into ClickHouse for testing."""
    backend = ClickHouseDatabase(
        host=CLICKHOUSE_TEST_HOST,
        port=CLICKHOUSE_TEST_PORT,
        database=CLICKHOUSE_TEST_DATABASE,
        event_table_name=CLICKHOUSE_TEST_TABLE_NAME,
    )
    success = backend.put(statements)
    assert success == len(statements)


@pytest.fixture(params=["es", "mongo", "clickhouse"])
# pylint: disable=unused-argument
def insert_statements_and_monkeypatch_backend(
    request, es, mongo, clickhouse, monkeypatch
):
    """(Security) Return a function that inserts statements into each backend."""
    # pylint: disable=invalid-name

    def _insert_statements_and_monkeypatch_backend(statements):
        """Insert statements once into each backend."""
        database_client_class_path = "ralph.api.routers.statements.DATABASE_CLIENT"
        if request.param == "mongo":
            insert_mongo_statements(mongo, statements)
            monkeypatch.setattr(database_client_class_path, get_mongo_test_backend())
            return
        if request.param == "clickhouse":
            insert_clickhouse_statements(statements)
            monkeypatch.setattr(
                database_client_class_path, get_clickhouse_test_backend()
            )
            return
        insert_es_statements(es, statements)
        monkeypatch.setattr(database_client_class_path, get_es_test_backend())

    return _insert_statements_and_monkeypatch_backend


@pytest.mark.parametrize(
    "ifi",
    [
        "mbox",
        "mbox_sha1sum",
        "openid",
        "account_same_home_page",
        "account_different_home_page",
    ],
)
def test_api_statements_get_mine(
    monkeypatch, fs, insert_statements_and_monkeypatch_backend, ifi
):
    """(Security) Test that the get statements API route, given a "mine=True"
    query parameter returns a list of statements filtered by authority.
    """
    # pylint: disable=redefined-outer-name
    # pylint: disable=invalid-name

    # Create two distinct agents
    if ifi == "account_same_home_page":
        agent_1 = create_mock_agent("account", 1, home_page_id=1)
        agent_1_bis = create_mock_agent(
            "account", 1, home_page_id=1, name="name", use_object_type=False
        )
        agent_2 = create_mock_agent("account", 2, home_page_id=1)
    elif ifi == "account_different_home_page":
        agent_1 = create_mock_agent("account", 1, home_page_id=1)
        agent_1_bis = create_mock_agent(
            "account", 1, home_page_id=1, name="name", use_object_type=False
        )
        agent_2 = create_mock_agent("account", 1, home_page_id=2)
    else:
        agent_1 = create_mock_agent(ifi, 1)
        agent_1_bis = create_mock_agent(ifi, 1, name="name", use_object_type=False)
        agent_2 = create_mock_agent(ifi, 2)

    username_1 = "jane"
    password_1 = "janepwd"
    scopes = []

    credentials_1_bis = create_mock_basic_auth_user(
        fs, username_1, password_1, scopes, agent_1_bis
    )

    # Clear cache before each test iteration
    get_basic_user.cache_clear()

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "actor": agent_1,
            "authority": agent_1,
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
            "actor": agent_1,
            "authority": agent_2,
        },
    ]
    insert_statements_and_monkeypatch_backend(statements)

    # No restriction on "mine" (implicit) : Return all statements
    response = client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    print('yeah')
    print(response.content)
    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1], statements[0]]}

    # No restriction on "mine" (explicit) : Return all statements
    response = client.get(
        "/xAPI/statements/?mine=False",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1], statements[0]]}

    # Only fetch mine (explicit) : Return filtered statements
    response = client.get(
        "/xAPI/statements/?mine=True",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}

    # Only fetch mine (implicit with RALPH_LRS_RESTRICT_BY_AUTHORITY=True): Return
    # filtered statements
    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.LRS_RESTRICT_BY_AUTHORITY", True
    )
    response = client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}

    # Only fetch mine (implicit) with contradictory user request: Return filtered
    # statements
    response = client.get(
        "/xAPI/statements/?mine=False",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}

    # Fetch "mine" by id with a single forbidden statement : Return empty list
    response = client.get(
        f"/xAPI/statements/?statementId={statements[1]['id']}&mine=True",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 200
    assert response.json() == {"statements": []}

    # Check that invalid parameters returns an error
    response = client.get(
        "/xAPI/statements/?mine=BigBoat",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 422


def test_api_statements_get(
    insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route without any filters set up."""
    # pylint: disable=redefined-outer-name

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
    insert_statements_and_monkeypatch_backend(statements)

    # Confirm that calling this with and without the trailing slash both work
    for path in ("/xAPI/statements", "/xAPI/statements/"):
        response = client.get(
            path, headers={"Authorization": f"Basic {basic_auth_credentials}"}
        )

        assert response.status_code == 200
        assert response.json() == {"statements": [statements[1], statements[0]]}


def test_api_statements_get_ascending(
    insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given an "ascending" query parameter, should
    return statements in ascending order by their timestamp.
    """
    # pylint: disable=redefined-outer-name

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
    insert_statements_and_monkeypatch_backend(statements)

    response = client.get(
        "/xAPI/statements/?ascending=true",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0], statements[1]]}


def test_api_statements_get_by_statement_id(
    insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given a "statementId" query parameter, should
    return a list of statements matching the given statementId.
    """
    # pylint: disable=redefined-outer-name

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
    insert_statements_and_monkeypatch_backend(statements)

    response = client.get(
        f"/xAPI/statements/?statementId={statements[1]['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


@pytest.mark.parametrize(
    "ifi",
    [
        "mbox",
        "mbox_sha1sum",
        "openid",
        "account_same_home_page",
        "account_different_home_page",
    ],
)
def test_api_statements_get_by_agent(
    ifi, insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given an "agent" query parameter, should
    return a list of statements filtered by the given agent.
    """
    # pylint: disable=redefined-outer-name

    # Create two distinct agents
    if ifi == "account_same_home_page":
        agent_1 = create_mock_agent("account", 1, home_page_id=1)
        agent_2 = create_mock_agent("account", 2, home_page_id=1)
    elif ifi == "account_different_home_page":
        agent_1 = create_mock_agent("account", 1, home_page_id=1)
        agent_2 = create_mock_agent("account", 1, home_page_id=2)
    else:
        agent_1 = create_mock_agent(ifi, 1)
        agent_2 = create_mock_agent(ifi, 2)

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": datetime.now().isoformat(),
            "actor": agent_1,
            "authority": agent_1,
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
            "actor": agent_2,
            "authority": agent_1,
        },
    ]
    insert_statements_and_monkeypatch_backend(statements)

    response = client.get(
        f"/xAPI/statements/?agent={quote_plus(json.dumps(agent_1))}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}


def test_api_statements_get_by_verb(
    insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given a "verb" query parameter, should
    return a list of statements filtered by the given verb id.
    """
    # pylint: disable=redefined-outer-name

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
    insert_statements_and_monkeypatch_backend(statements)

    response = client.get(
        "/xAPI/statements/?verb=" + quote_plus("http://adlnet.gov/expapi/verbs/played"),
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


def test_api_statements_get_by_activity(
    insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given an "activity" query parameter, should
    return a list of statements filtered by the given activity id.
    """
    # pylint: disable=redefined-outer-name

    activity_0 = create_mock_activity(0)
    activity_1 = create_mock_activity(1)

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": datetime.now().isoformat(),
            "object": activity_0,
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
            "object": activity_1,
        },
    ]
    insert_statements_and_monkeypatch_backend(statements)

    response = client.get(
        f"/xAPI/statements/?activity={activity_1['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}

    # Check that badly formated activity returns an error
    response = client.get(
        "/xAPI/statements/?activity=INVALID_IRI",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "'INVALID_IRI' is not a valid 'IRI'."


def test_api_statements_get_since_timestamp(
    insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given a "since" query parameter, should
    return a list of statements filtered by the given timestamp.
    """
    # pylint: disable=redefined-outer-name

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
    insert_statements_and_monkeypatch_backend(statements)

    since = (datetime.now() - timedelta(minutes=30)).isoformat()
    response = client.get(
        f"/xAPI/statements/?since={since}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


def test_api_statements_get_until_timestamp(
    insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given an "until" query parameter,
    should return a list of statements filtered by the given timestamp.
    """
    # pylint: disable=redefined-outer-name

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
    insert_statements_and_monkeypatch_backend(statements)

    until = (datetime.now() - timedelta(minutes=30)).isoformat()
    response = client.get(
        f"/xAPI/statements/?until={until}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}


def test_api_statements_get_with_pagination(
    monkeypatch, insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given a request leading to more results than
    can fit on the first page, should return a list of statements non-exceeding the page
    limit and include a "more" property with a link to get the next page of results.
    """
    # pylint: disable=redefined-outer-name

    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.RUNSERVER_MAX_SEARCH_HITS_COUNT", 2
    )

    statements = [
        {
            "id": "5d345b99-517c-4b54-848e-45010904b177",
            "timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
        },
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),
        },
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac5",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
        },
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac4",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
        },
    ]
    insert_statements_and_monkeypatch_backend(statements)

    # First response gets the first two results, with a "more" entry as
    # we have more results to return on a later page.
    first_response = client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert first_response.status_code == 200
    assert first_response.json()["statements"] == [statements[4], statements[3]]
    more = urlparse(first_response.json()["more"])
    more_query_params = parse_qs(more.query)
    assert more.path == "/xAPI/statements/"
    assert all(key in more_query_params for key in ("pit_id", "search_after"))

    # Second response gets the missing result from the first response.
    second_response = client.get(
        first_response.json()["more"],
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert second_response.status_code == 200
    assert second_response.json()["statements"] == [statements[2], statements[1]]
    more = urlparse(first_response.json()["more"])
    more_query_params = parse_qs(more.query)
    assert more.path == "/xAPI/statements/"
    assert all(key in more_query_params for key in ("pit_id", "search_after"))

    # Third response gets the missing result from the first response
    third_response = client.get(
        second_response.json()["more"],
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert third_response.status_code == 200
    assert third_response.json() == {"statements": [statements[0]]}


def test_api_statements_get_with_pagination_and_query(
    monkeypatch, insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given a request with a query parameter
    leading to more results than can fit on the first page, should return a list
    of statements non-exceeding the page limit and include a "more" property with
    a link to get the next page of results.
    """
    # pylint: disable=redefined-outer-name

    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.RUNSERVER_MAX_SEARCH_HITS_COUNT", 2
    )

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "verb": {
                "id": "https://w3id.org/xapi/video/verbs/played",
                "display": {"en-US": "played"},
            },
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
        },
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac1",
            "verb": {
                "id": "https://w3id.org/xapi/video/verbs/played",
                "display": {"en-US": "played"},
            },
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "verb": {
                "id": "https://w3id.org/xapi/video/verbs/played",
                "display": {"en-US": "played"},
            },
            "timestamp": datetime.now().isoformat(),
        },
    ]
    insert_statements_and_monkeypatch_backend(statements)

    # First response gets the first two results, with a "more" entry as
    # we have more results to return on a later page.
    first_response = client.get(
        "/xAPI/statements/?verb="
        + quote_plus("https://w3id.org/xapi/video/verbs/played"),
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert first_response.status_code == 200
    assert first_response.json()["statements"] == [statements[2], statements[1]]
    more = urlparse(first_response.json()["more"])
    more_query_params = parse_qs(more.query)
    assert more.path == "/xAPI/statements/"
    assert all(key in more_query_params for key in ("verb", "pit_id", "search_after"))

    # Second response gets the missing result from the first response.
    second_response = client.get(
        first_response.json()["more"],
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert second_response.status_code == 200
    assert second_response.json() == {"statements": [statements[0]]}


def test_api_statements_get_with_no_matching_statement(
    insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given a query yielding no matching statement,
    should return an empty list.
    """
    # pylint: disable=redefined-outer-name

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
    insert_statements_and_monkeypatch_backend(statements)

    response = client.get(
        "/xAPI/statements/?statementId=66c81e98-1763-4730-8cfc-f5ab34f1bad5",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": []}


def test_api_statements_get_with_database_query_failure(
    basic_auth_credentials, monkeypatch
):
    """Test the get statements API route, given a query raising a BackendException,
    should return an error response with HTTP code 500.
    """
    # pylint: disable=redefined-outer-name

    def mock_query_statements(*_):
        """Mock the DATABASE_CLIENT.query_statements method."""
        raise BackendException()

    monkeypatch.setattr(
        "ralph.api.routers.statements.DATABASE_CLIENT.query_statements",
        mock_query_statements,
    )

    response = client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": "xAPI statements query failed"}


@pytest.mark.parametrize("id_param", ["statementId", "voidedStatementId"])
def test_api_statements_get_invalid_query_parameters(basic_auth_credentials, id_param):
    """Test error response for invalid query parameters"""

    id_1 = "be67b160-d958-4f51-b8b8-1892002dbac6"
    id_2 = "66c81e98-1763-4730-8cfc-f5ab34f1bad5"

    # Check for 400 status code when unknown parameters are provided
    response = client.get(
        "/xAPI/statements/?mamamia=herewegoagain",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "The following parameter is not allowed: `mamamia`"
    }

    # Check for 400 status code when both statementId and voidedStatementId are provided
    response = client.get(
        f"/xAPI/statements/?statementId={id_1}&voidedStatementId={id_2}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert response.status_code == 400

    # Check for 400 status code when invalid parameters are provided with a statementId
    for invalid_param, value in [
        ("activity", create_mock_activity()["id"]),
        ("agent", json.dumps(create_mock_agent("mbox", 1))),
        ("verb", "verb_1"),
    ]:
        response = client.get(
            f"/xAPI/statements/?{id_param}={id_1}&{invalid_param}={value}",
            headers={"Authorization": f"Basic {basic_auth_credentials}"},
        )
        assert response.status_code == 400
        assert response.json() == {
            "detail": (
                "Querying by id only accepts `attachments` and `format` as "
                "extra parameters"
            )
        }

    # Check for NO 400 status code when statementId is passed with authorized parameters
    for valid_param, value in [("format", "ids"), ("attachments", "true")]:
        response = client.get(
            f"/xAPI/statements/?{id_param}={id_1}&{valid_param}={value}",
            headers={"Authorization": f"Basic {basic_auth_credentials}"},
        )
        assert response.status_code != 400


@responses.activate
@pytest.mark.parametrize("auth_method", ["basic", "oidc"])
@pytest.mark.parametrize(
    "scopes,is_authorized",
    [
        (["all"], True),
        (["all/read"], True),
        (["statements/read/mine"], True),
        (["statements/read"], True),
        (["profile/write", "all/write", "statements/read"], True),
        (["statements/write"], False),
        (["profile/read"], False),
        (["all/write"], False),
        ([], False),
    ],
)
def test_api_statements_get_scopes(
    monkeypatch, fs, es, auth_method, scopes, is_authorized
):
    """Test that getting statements behaves properly according to user scopes."""
    # pylint: disable=invalid-name
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-arguments

    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.LRS_RESTRICT_BY_SCOPES", True
    )
    monkeypatch.setattr("ralph.api.auth.basic.settings.LRS_RESTRICT_BY_SCOPES", True)

    if auth_method == "basic":
        agent = create_mock_agent("mbox", 1)
        credentials = create_mock_basic_auth_user(fs, scopes=scopes, agent=agent)
        headers = {"Authorization": f"Basic {credentials}"}

        app.dependency_overrides[get_authenticated_user] = get_basic_user
        get_basic_user.cache_clear()

    elif auth_method == "oidc":
        sub = "123|oidc"
        agent = {"openid": sub}
        oidc_token = create_mock_oidc_user(sub=sub, scopes=scopes)
        headers = {"Authorization": f"Bearer {oidc_token}"}

        monkeypatch.setattr(
            "ralph.api.auth.oidc.settings.RUNSERVER_AUTH_OIDC_ISSUER_URI",
            "http://providerHost:8080/auth/realms/real_name",
        )
        monkeypatch.setattr(
            "ralph.api.auth.oidc.settings.RUNSERVER_AUTH_OIDC_AUDIENCE",
            "http://clientHost:8100",
        )

        app.dependency_overrides[get_authenticated_user] = get_oidc_user

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "actor": agent,
            "authority": agent,
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
            "actor": agent,
            "authority": agent,
        },
    ]

    # NB: scopes are not linked to statements and backends, we therefore test with ES
    database_client_class_path = "ralph.api.routers.statements.DATABASE_CLIENT"
    insert_es_statements(es, statements)
    monkeypatch.setattr(database_client_class_path, get_es_test_backend())

    response = client.get(
        "/xAPI/statements/",
        headers=headers,
    )

    if is_authorized:
        assert response.status_code == 200
        assert response.json() == {"statements": [statements[1], statements[0]]}
    else:
        assert response.status_code == 401
        assert response.json() == {
            "detail": 'Access not authorized to scope: "statements/read/mine".'
        }

    app.dependency_overrides.pop(get_authenticated_user, None)


@pytest.mark.parametrize(
    "scopes,read_all_access",
    [
        (["all"], True),
        (["all/read", "statements/read/mine"], True),
        (["statements/read"], True),
        (["statements/read/mine"], False),
    ],
)
def test_api_statements_get_scopes_with_authority(
    monkeypatch, fs, es, scopes, read_all_access
):
    """Test that restricting by scope and by authority behaves properly.

    Getting statements should be restricted to mine for users which only have
    `statements/read/mine` scope but should not be restricted when the user
    has wider scopes.
    """
    # pylint: disable=invalid-name
    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.LRS_RESTRICT_BY_AUTHORITY", True
    )
    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.LRS_RESTRICT_BY_SCOPES", True
    )
    monkeypatch.setattr("ralph.api.auth.basic.settings.LRS_RESTRICT_BY_SCOPES", True)

    agent = create_mock_agent("mbox", 1)
    agent_2 = create_mock_agent("mbox", 2)
    username = "jane"
    password = "janepwd"
    credentials = create_mock_basic_auth_user(fs, username, password, scopes, agent)
    headers = {"Authorization": f"Basic {credentials}"}

    get_basic_user.cache_clear()

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "actor": agent,
            "authority": agent,
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
            "actor": agent,
            "authority": agent_2,
        },
    ]

    # NB: scopes are not linked to statements and backends, we therefore test with ES
    database_client_class_path = "ralph.api.routers.statements.DATABASE_CLIENT"
    insert_es_statements(es, statements)
    monkeypatch.setattr(database_client_class_path, get_es_test_backend())

    response = client.get(
        "/xAPI/statements/",
        headers=headers,
    )

    assert response.status_code == 200

    if read_all_access:
        assert response.json() == {"statements": [statements[1], statements[0]]}
    else:
        assert response.json() == {"statements": [statements[0]]}

    app.dependency_overrides.pop(get_authenticated_user, None)
