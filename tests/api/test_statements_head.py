"""Tests for the HEAD statements endpoint of the Ralph API."""

import json
from datetime import datetime, timedelta

import pytest

from ralph.exceptions import BackendException

from tests.fixtures.backends import get_es_test_backend

from ..helpers import mock_activity, mock_agent


@pytest.mark.anyio
async def test_api_statements_head(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the head statements API route without any filters set up."""

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
        response = await client.head(
            path, headers={"Authorization": f"Basic {basic_auth_credentials}"}
        )

        assert response.status_code == 200
        assert len(response.content) == 0


@pytest.mark.anyio
async def test_api_statements_head_by_statement_id(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the head statements API route given a "statementId" query parameter."""

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

    response = await client.head(
        f"/xAPI/statements/?statementId={statements[1]['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert len(response.content) == 0


@pytest.mark.anyio
async def test_api_statements_head_with_no_matching_statement(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """
    Test the head statements API route, given a query yielding no matching statement.
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
    insert_statements_and_monkeypatch_backend(statements)

    response = await client.head(
        "/xAPI/statements/?statementId=66c81e98-1763-4730-8cfc-f5ab34f1bad5",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert len(response.content) == 0


@pytest.mark.anyio
async def test_api_statements_head_with_database_query_failure(
    client, basic_auth_credentials, monkeypatch
):
    """Test the head statements API route, given a query raising a BackendException."""

    def mock_query_statements(*_, **__):
        """Mocks the BACKEND_CLIENT.query_statements method."""
        raise BackendException()

    monkeypatch.setattr(
        "ralph.api.routers.statements.BACKEND_CLIENT.query_statements",
        mock_query_statements,
    )

    response = await client.head(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert response.status_code == 500
    assert len(response.content) == 0


@pytest.mark.anyio
@pytest.mark.parametrize("id_param", ["statementId", "voidedStatementId"])
async def test_api_statements_head_invalid_query_parameters(
    client, monkeypatch, es, basic_auth_credentials, id_param
):
    """Test error response for invalid query parameters."""

    id_1 = "be67b160-d958-4f51-b8b8-1892002dbac6"
    id_2 = "66c81e98-1763-4730-8cfc-f5ab34f1bad5"

    # Check for 400 status code when unknown parameters are provided
    response = await client.head(
        "/xAPI/statements/?mamamia=herewegoagain",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert response.status_code == 400
    assert len(response.content) == 0

    # Check for 400 status code when a negative limit parameter is provided
    response = await client.head(
        "/xAPI/statements/?limit=-1",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert response.status_code == 400

    # Check for 400 status code when both statementId and voidedStatementId are provided
    response = await client.head(
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
        response = await client.head(
            f"/xAPI/statements/?{id_param}={id_1}&{invalid_param}={value}",
            headers={"Authorization": f"Basic {basic_auth_credentials}"},
        )
        assert response.status_code == 400
        assert len(response.content) == 0

    backend_client_class_path = "ralph.api.routers.statements.BACKEND_CLIENT"
    monkeypatch.setattr(backend_client_class_path, get_es_test_backend())

    # Check for NO 400 status code when statementId is passed with authorized parameters
    for valid_param, value in [("format", "ids"), ("attachments", "true")]:
        response = await client.head(
            f"/xAPI/statements/?{id_param}={id_1}&{valid_param}={value}",
            headers={"Authorization": f"Basic {basic_auth_credentials}"},
        )
        assert response.status_code != 400
