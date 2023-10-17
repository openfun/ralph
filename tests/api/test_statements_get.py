"""Tests for the GET statements endpoint of the Ralph API."""

import json
from datetime import datetime, timedelta
from urllib.parse import parse_qs, quote_plus, urlparse

import pytest
import responses
from elasticsearch.helpers import bulk

from ralph.api import app
from ralph.api.auth import get_authenticated_user
from ralph.api.auth.basic import get_basic_auth_user
from ralph.api.auth.oidc import get_oidc_user
from ralph.backends.data.base import BaseOperationType
from ralph.backends.data.clickhouse import ClickHouseDataBackend
from ralph.backends.data.mongo import MongoDataBackend
from ralph.exceptions import BackendException

from tests.fixtures.backends import (
    CLICKHOUSE_TEST_DATABASE,
    CLICKHOUSE_TEST_HOST,
    CLICKHOUSE_TEST_PORT,
    CLICKHOUSE_TEST_TABLE_NAME,
    ES_TEST_INDEX,
    MONGO_TEST_COLLECTION,
    MONGO_TEST_DATABASE,
    get_async_es_test_backend,
    get_async_mongo_test_backend,
    get_clickhouse_test_backend,
    get_es_test_backend,
    get_mongo_test_backend,
)

from ..fixtures.auth import mock_basic_auth_user, mock_oidc_user
from ..helpers import mock_activity, mock_agent


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
    collection.insert_many(
        list(
            MongoDataBackend.to_documents(
                data=statements,
                ignore_errors=True,
                operation_type=BaseOperationType.CREATE,
                logger_class=None,
            )
        )
    )


def insert_clickhouse_statements(statements):
    """Inserts a bunch of example statements into ClickHouse for testing."""
    settings = ClickHouseDataBackend.settings_class(
        HOST=CLICKHOUSE_TEST_HOST,
        PORT=CLICKHOUSE_TEST_PORT,
        DATABASE=CLICKHOUSE_TEST_DATABASE,
        EVENT_TABLE_NAME=CLICKHOUSE_TEST_TABLE_NAME,
    )
    backend = ClickHouseDataBackend(settings=settings)
    success = backend.write(statements)
    assert success == len(statements)


@pytest.fixture(params=["async_es", "async_mongo", "es", "mongo", "clickhouse"])
def insert_statements_and_monkeypatch_backend(
    request, es, mongo, clickhouse, monkeypatch
):
    """(Security) Return a function that inserts statements into each backend."""
    # pylint: disable=invalid-name,unused-argument

    def _insert_statements_and_monkeypatch_backend(statements):
        """Inserts statements once into each backend."""
        backend_client_class_path = "ralph.api.routers.statements.BACKEND_CLIENT"
        if request.param == "async_es":
            insert_es_statements(es, statements)
            monkeypatch.setattr(backend_client_class_path, get_async_es_test_backend())
            return
        if request.param == "async_mongo":
            insert_mongo_statements(mongo, statements)
            monkeypatch.setattr(
                backend_client_class_path, get_async_mongo_test_backend()
            )
            return
        if request.param == "es":
            insert_es_statements(es, statements)
            monkeypatch.setattr(backend_client_class_path, get_es_test_backend())
            return
        if request.param == "mongo":
            insert_mongo_statements(mongo, statements)
            monkeypatch.setattr(backend_client_class_path, get_mongo_test_backend())
            return
        if request.param == "clickhouse":
            insert_clickhouse_statements(statements)
            monkeypatch.setattr(
                backend_client_class_path, get_clickhouse_test_backend()
            )
            return

    return _insert_statements_and_monkeypatch_backend


@pytest.mark.anyio
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
async def test_api_statements_get_mine(
    client, monkeypatch, fs, insert_statements_and_monkeypatch_backend, ifi
):
    """(Security) Test that the get statements API route, given a "mine=True"
    query parameter returns a list of statements filtered by authority.
    """
    # pylint: disable=redefined-outer-name,invalid-name

    # Create two distinct agents
    if ifi == "account_same_home_page":
        agent_1 = mock_agent("account", 1, home_page_id=1)
        agent_1_bis = mock_agent(
            "account", 1, home_page_id=1, name="name", use_object_type=False
        )
        agent_2 = mock_agent("account", 2, home_page_id=1)
    elif ifi == "account_different_home_page":
        agent_1 = mock_agent("account", 1, home_page_id=1)
        agent_1_bis = mock_agent(
            "account", 1, home_page_id=1, name="name", use_object_type=False
        )
        agent_2 = mock_agent("account", 1, home_page_id=2)
    else:
        agent_1 = mock_agent(ifi, 1)
        agent_1_bis = mock_agent(ifi, 1, name="name", use_object_type=False)
        agent_2 = mock_agent(ifi, 2)

    username_1 = "jane"
    password_1 = "janepwd"
    scopes = []

    credentials_1_bis = mock_basic_auth_user(
        fs, username_1, password_1, scopes, agent_1_bis
    )

    # Clear cache before each test iteration
    get_basic_auth_user.cache_clear()

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
    response = await client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1], statements[0]]}

    # No restriction on "mine" (explicit) : Return all statements
    response = await client.get(
        "/xAPI/statements/?mine=False",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1], statements[0]]}

    # Only fetch mine (explicit) : Return filtered statements
    response = await client.get(
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
    response = await client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}

    # Only fetch mine (implicit) with contradictory user request: Return filtered
    # statements
    response = await client.get(
        "/xAPI/statements/?mine=False",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}

    # Fetch "mine" by id with a single forbidden statement : Return empty list
    response = await client.get(
        f"/xAPI/statements/?statementId={statements[1]['id']}&mine=True",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 200
    assert response.json() == {"statements": []}

    # Check that invalid parameters returns an error
    response = await client.get(
        "/xAPI/statements/?mine=BigBoat",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_api_statements_get(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
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
        response = await client.get(
            path, headers={"Authorization": f"Basic {basic_auth_credentials}"}
        )

        assert response.status_code == 200
        assert response.json() == {"statements": [statements[1], statements[0]]}


@pytest.mark.anyio
async def test_api_statements_get_ascending(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
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

    response = await client.get(
        "/xAPI/statements/?ascending=true",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0], statements[1]]}


@pytest.mark.anyio
async def test_api_statements_get_by_statement_id(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
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

    response = await client.get(
        f"/xAPI/statements/?statementId={statements[1]['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


@pytest.mark.anyio
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
async def test_api_statements_get_by_agent(
    client, ifi, insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given an "agent" query parameter, should
    return a list of statements filtered by the given agent.
    """
    # pylint: disable=redefined-outer-name

    # Create two distinct agents
    if ifi == "account_same_home_page":
        agent_1 = mock_agent("account", 1, home_page_id=1)
        agent_2 = mock_agent("account", 2, home_page_id=1)
    elif ifi == "account_different_home_page":
        agent_1 = mock_agent("account", 1, home_page_id=1)
        agent_2 = mock_agent("account", 1, home_page_id=2)
    else:
        agent_1 = mock_agent(ifi, 1)
        agent_2 = mock_agent(ifi, 2)

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

    response = await client.get(
        f"/xAPI/statements/?agent={quote_plus(json.dumps(agent_1))}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}


@pytest.mark.anyio
async def test_api_statements_get_by_verb(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
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

    response = await client.get(
        "/xAPI/statements/?verb=" + quote_plus("http://adlnet.gov/expapi/verbs/played"),
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


@pytest.mark.anyio
async def test_api_statements_get_by_activity(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given an "activity" query parameter, should
    return a list of statements filtered by the given activity id.
    """
    # pylint: disable=redefined-outer-name

    activity_0 = mock_activity(0)
    activity_1 = mock_activity(1)

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

    response = await client.get(
        f"/xAPI/statements/?activity={activity_1['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}

    # Check that badly formated activity returns an error
    response = await client.get(
        "/xAPI/statements/?activity=INVALID_IRI",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "'INVALID_IRI' is not a valid 'IRI'."


@pytest.mark.anyio
async def test_api_statements_get_since_timestamp(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
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
    response = await client.get(
        f"/xAPI/statements/?since={since}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


@pytest.mark.anyio
async def test_api_statements_get_until_timestamp(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
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
    response = await client.get(
        f"/xAPI/statements/?until={until}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}


@pytest.mark.anyio
async def test_api_statements_get_with_pagination(
    client,
    monkeypatch,
    insert_statements_and_monkeypatch_backend,
    basic_auth_credentials,
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
    first_response = await client.get(
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
    second_response = await client.get(
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
    third_response = await client.get(
        second_response.json()["more"],
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert third_response.status_code == 200
    assert third_response.json() == {"statements": [statements[0]]}


@pytest.mark.anyio
async def test_api_statements_get_with_pagination_and_query(
    client,
    monkeypatch,
    insert_statements_and_monkeypatch_backend,
    basic_auth_credentials,
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
    first_response = await client.get(
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
    second_response = await client.get(
        first_response.json()["more"],
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert second_response.status_code == 200
    assert second_response.json() == {"statements": [statements[0]]}


@pytest.mark.anyio
async def test_api_statements_get_with_no_matching_statement(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
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

    response = await client.get(
        "/xAPI/statements/?statementId=66c81e98-1763-4730-8cfc-f5ab34f1bad5",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": []}


@pytest.mark.anyio
async def test_api_statements_get_with_database_query_failure(
    client, basic_auth_credentials, monkeypatch
):
    """Test the get statements API route, given a query raising a BackendException,
    should return an error response with HTTP code 500.
    """
    # pylint: disable=redefined-outer-name

    def mock_query_statements(*_):
        """Mocks the BACKEND_CLIENT.query_statements method."""
        raise BackendException()

    monkeypatch.setattr(
        "ralph.api.routers.statements.BACKEND_CLIENT.query_statements",
        mock_query_statements,
    )

    response = await client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": "xAPI statements query failed"}


@pytest.mark.anyio
@pytest.mark.parametrize("id_param", ["statementId", "voidedStatementId"])
async def test_api_statements_get_invalid_query_parameters(
    client, basic_auth_credentials, id_param
):
    """Test error response for invalid query parameters"""

    id_1 = "be67b160-d958-4f51-b8b8-1892002dbac6"
    id_2 = "66c81e98-1763-4730-8cfc-f5ab34f1bad5"

    # Check for 400 status code when unknown parameters are provided
    response = await client.get(
        "/xAPI/statements/?mamamia=herewegoagain",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "The following parameter is not allowed: `mamamia`"
    }

    # Check for 400 status code when both statementId and voidedStatementId are provided
    response = await client.get(
        f"/xAPI/statements/?statementId={id_1}&voidedStatementId={id_2}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert response.status_code == 400

    # Check for 400 status code when invalid parameters are provided with a statementId
    for invalid_param, value in [
        ("activity", mock_activity()["id"]),
        ("agent", json.dumps(mock_agent("mbox", 1))),
        ("verb", "verb_1"),
    ]:
        response = await client.get(
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
        response = await client.get(
            f"/xAPI/statements/?{id_param}={id_1}&{valid_param}={value}",
            headers={"Authorization": f"Basic {basic_auth_credentials}"},
        )
        assert response.status_code != 400


@pytest.mark.anyio
@responses.activate
@pytest.mark.parametrize("auth_method", ["basic", "oidc"])
@pytest.mark.parametrize(
    "scopes,is_authorized",
    [
        (["all"], True),
        (["all/read"], True),
        (["statements/read/mine"], True),
        (["statements/read"], True),
        (["profile/write", "statements/read", "all/write"], True),
        (["statements/write"], False),
        (["profile/read"], False),
        (["all/write"], False),
        ([], False),
    ],
)
async def test_api_statements_get_scopes(
    client, monkeypatch, fs, es, auth_method, scopes, is_authorized
):
    """Test that getting statements behaves properly according to user scopes."""
    # pylint: disable=invalid-name,too-many-locals,too-many-arguments

    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.LRS_RESTRICT_BY_SCOPES", True
    )
    monkeypatch.setattr("ralph.api.auth.basic.settings.LRS_RESTRICT_BY_SCOPES", True)

    if auth_method == "basic":
        agent = mock_agent("mbox", 1)
        credentials = mock_basic_auth_user(fs, scopes=scopes, agent=agent)
        headers = {"Authorization": f"Basic {credentials}"}

        app.dependency_overrides[get_authenticated_user] = get_basic_auth_user
        get_basic_auth_user.cache_clear()

    elif auth_method == "oidc":
        sub = "123|oidc"
        iss = "https://iss.example.com"
        agent = {"openid": f"{iss}/{sub}"}
        oidc_token = mock_oidc_user(sub=sub, scopes=scopes)
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
    backend_client_class_path = "ralph.api.routers.statements.BACKEND_CLIENT"
    insert_es_statements(es, statements)
    monkeypatch.setattr(backend_client_class_path, get_es_test_backend())

    response = await client.get(
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


@pytest.mark.anyio
@pytest.mark.parametrize(
    "scopes,read_all_access",
    [
        (["all"], True),
        (["all/read", "statements/read/mine"], True),
        (["statements/read"], True),
        (["statements/read/mine"], False),
    ],
)
async def test_api_statements_get_scopes_with_authority(
    client, monkeypatch, fs, es, scopes, read_all_access
):
    """Test that restricting by scope and by authority behaves properly.
    Getting statements should be restricted to mine for users which only have
    `statements/read/mine` scope but should not be restricted when the user
    has wider scopes.
    """
    # pylint: disable=invalid-name,too-many-arguments
    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.LRS_RESTRICT_BY_AUTHORITY", True
    )
    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.LRS_RESTRICT_BY_SCOPES", True
    )
    monkeypatch.setattr("ralph.api.auth.basic.settings.LRS_RESTRICT_BY_SCOPES", True)

    agent = mock_agent("mbox", 1)
    agent_2 = mock_agent("mbox", 2)
    username = "jane"
    password = "janepwd"
    credentials = mock_basic_auth_user(fs, username, password, scopes, agent)
    headers = {"Authorization": f"Basic {credentials}"}

    get_basic_auth_user.cache_clear()

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
    backend_client_class_path = "ralph.api.routers.statements.BACKEND_CLIENT"
    insert_es_statements(es, statements)
    monkeypatch.setattr(backend_client_class_path, get_es_test_backend())

    response = await client.get(
        "/xAPI/statements/",
        headers=headers,
    )

    assert response.status_code == 200

    if read_all_access:
        assert response.json() == {"statements": [statements[1], statements[0]]}
    else:
        assert response.json() == {"statements": [statements[0]]}

    app.dependency_overrides.pop(get_authenticated_user, None)
