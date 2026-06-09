"""Tests for POST /xAPI/statements?partialSuccess=true."""

from uuid import uuid4

import pytest

from tests.fixtures.backends import (
    get_async_es_test_backend,
    get_es_test_backend,
)

from ..helpers import mock_statement


def _mixed_batch():
    good = mock_statement()
    bad = {"verb": {"id": "http://example.com/verb"}, "object": {"id": "http://ex.com/o"}}
    good2 = mock_statement()
    return [good, bad, good2]


@pytest.mark.anyio
@pytest.mark.parametrize("backend", [get_async_es_test_backend, get_es_test_backend])
@pytest.mark.parametrize("flag", ["partialSuccess=true", "ignoreInvalid=true"])
async def test_api_statements_post_partial_success_inserts_valid_only(
    client, backend, monkeypatch, basic_auth_credentials, es, flag
):
    """Valid statements are stored; invalid ones are reported."""
    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())
    batch = _mixed_batch()

    response = await client.post(
        f"/xAPI/statements/?{flag}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=batch,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["inserted"] == 2
    assert payload["rejected"] == 1
    assert len(payload["ids"]) == 2
    assert payload["errors"][0]["index"] == 1
    assert "actor" in payload["errors"][0]["reason"].lower()

    es.indices.refresh()
    get_response = await client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert get_response.status_code == 200
    assert len(get_response.json()["statements"]) == 2


@pytest.mark.anyio
@pytest.mark.parametrize("backend", [get_async_es_test_backend, get_es_test_backend])
async def test_api_statements_post_partial_success_all_invalid(
    client, backend, monkeypatch, basic_auth_credentials, es
):
    """When every statement is invalid the LRS returns 400 with a report."""
    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())

    response = await client.post(
        "/xAPI/statements/?partialSuccess=true",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=[{"foo": "bar"}, {}],
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["inserted"] == 0
    assert payload["rejected"] == 2
    assert len(payload["errors"]) == 2


@pytest.mark.anyio
@pytest.mark.parametrize("backend", [get_async_es_test_backend, get_es_test_backend])
async def test_api_statements_post_strict_still_rejects_batch(
    client, backend, monkeypatch, basic_auth_credentials, es
):
    """Without the flag, a mixed batch is rejected atomically."""
    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())

    response = await client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=_mixed_batch(),
    )

    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.anyio
@pytest.mark.parametrize("backend", [get_async_es_test_backend, get_es_test_backend])
async def test_api_statements_post_partial_success_duplicate_ids_in_batch(
    client, backend, monkeypatch, basic_auth_credentials, es
):
    """Duplicate IDs in the same batch are reported, first occurrence is kept."""
    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())
    statement_id = str(uuid4())
    first = mock_statement(id_=statement_id)
    second = mock_statement(id_=statement_id)

    response = await client.post(
        "/xAPI/statements/?partialSuccess=true",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=[first, second],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["inserted"] == 1
    assert payload["rejected"] == 1
    assert payload["errors"][0]["index"] == 1


@pytest.mark.anyio
async def test_api_statements_post_partial_success_unknown_query_param_still_blocked(
    client, basic_auth_credentials
):
    """partialSuccess is allowed; other unknown params are not."""
    statement = mock_statement()
    response = await client.post(
        "/xAPI/statements/?partialSuccess=true&notAllowed=1",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )
    assert response.status_code == 400
    assert "notAllowed" in response.json()["detail"]
