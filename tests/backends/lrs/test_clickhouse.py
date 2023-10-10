"""Tests for Ralph clickhouse database backend."""

import logging
import uuid
from datetime import datetime, timezone

import pytest
from clickhouse_connect.driver.exceptions import ClickHouseError

from ralph.backends.lrs.base import RalphStatementsQuery
from ralph.exceptions import BackendException


@pytest.mark.parametrize(
    "params,expected_params",
    [
        # 0. Default query.
        (
            {},
            {
                "where": [],
                "params": {
                    "ascending": False,
                    "attachments": False,
                    "format": "exact",
                    "limit": 0,
                    "related_activities": False,
                    "related_agents": False,
                },
                "limit": 0,
                "sort": "emission_time DESCENDING, event_id DESCENDING",
            },
        ),
        # 1. Query by statementId.
        (
            {"statementId": "test_id"},
            {
                "where": ["event_id = {statementId:UUID}"],
                "params": {
                    "ascending": False,
                    "attachments": False,
                    "format": "exact",
                    "limit": 0,
                    "related_activities": False,
                    "related_agents": False,
                    "statementId": "test_id",
                    "statement_id": "test_id",
                },
                "limit": 0,
                "sort": "emission_time DESCENDING, event_id DESCENDING",
            },
        ),
        # # 2. Query by statementId and agent with mbox IFI.
        (
            {"statementId": "test_id", "agent": {"mbox": "mailto:foo@bar.baz"}},
            {
                "where": [
                    "event_id = {statementId:UUID}",
                    "event.actor.mbox = {actor__mbox:String}",
                ],
                "params": {
                    "actor__mbox": "mailto:foo@bar.baz",
                    "ascending": False,
                    "attachments": False,
                    "format": "exact",
                    "limit": 0,
                    "related_activities": False,
                    "related_agents": False,
                    "statementId": "test_id",
                    "statement_id": "test_id",
                },
                "limit": 0,
                "sort": "emission_time DESCENDING, event_id DESCENDING",
            },
        ),
        # # 3. Query by statementId and agent with mbox_sha1sum IFI.
        (
            {
                "statementId": "test_id",
                "agent": {"mbox_sha1sum": "a7a5b7462b862c8c8767d43d43e865ffff754a64"},
            },
            {
                "where": [
                    "event_id = {statementId:UUID}",
                    "event.actor.mbox_sha1sum = {actor__mbox_sha1sum:String}",
                ],
                "params": {
                    "actor__mbox_sha1sum": "a7a5b7462b862c8c8767d43d43e865ffff754a64",
                    "ascending": False,
                    "attachments": False,
                    "format": "exact",
                    "limit": 0,
                    "related_activities": False,
                    "related_agents": False,
                    "statementId": "test_id",
                    "statement_id": "test_id",
                },
                "limit": 0,
                "sort": "emission_time DESCENDING, event_id DESCENDING",
            },
        ),
        # 4. Query by statementId and agent with openid IFI.
        (
            {
                "statementId": "test_id",
                "agent": {"openid": "http://toby.openid.example.org/"},
            },
            {
                "where": [
                    "event_id = {statementId:UUID}",
                    "event.actor.openid = {actor__openid:String}",
                ],
                "params": {
                    "actor__openid": "http://toby.openid.example.org/",
                    "ascending": False,
                    "attachments": False,
                    "format": "exact",
                    "limit": 0,
                    "related_activities": False,
                    "related_agents": False,
                    "statementId": "test_id",
                    "statement_id": "test_id",
                },
                "limit": 0,
                "sort": "emission_time DESCENDING, event_id DESCENDING",
            },
        ),
        # 5. Query by statementId and agent with account IFI.
        (
            {
                "statementId": "test_id",
                "agent": {
                    "account__home_page": "http://www.example.com",
                    "account__name": "13936749",
                },
                "ascending": True,
            },
            {
                "where": [
                    "event_id = {statementId:UUID}",
                    "event.actor.account.name = {actor__account__name:String}",
                    "event.actor.account.homePage = {actor__account_home_page:String}",
                ],
                "params": {
                    "actor__account__name": "13936749",
                    "actor__account_home_page": "http://www.example.com",
                    "ascending": True,
                    "attachments": False,
                    "format": "exact",
                    "limit": 0,
                    "related_activities": False,
                    "related_agents": False,
                    "statementId": "test_id",
                    "statement_id": "test_id",
                },
                "limit": 0,
                "sort": "emission_time ASCENDING, event_id ASCENDING",
            },
        ),
        # 6. Query by verb and activity with limit.
        (
            {
                "verb": "http://adlnet.gov/expapi/verbs/attended",
                "activity": "http://www.example.com/meetings/34534",
                "limit": 100,
            },
            {
                "where": [
                    "event.verb.id = {verb:String}",
                    "event.object.objectType = 'Activity'",
                    "event.object.id = {activity:String}",
                ],
                "params": {
                    "ascending": False,
                    "activity": "http://www.example.com/meetings/34534",
                    "attachments": False,
                    "format": "exact",
                    "limit": 100,
                    "related_activities": False,
                    "related_agents": False,
                    "verb": "http://adlnet.gov/expapi/verbs/attended",
                },
                "limit": 100,
                "sort": "emission_time DESCENDING, event_id DESCENDING",
            },
        ),
        # 7. Query by timerange (with since/until).
        (
            {
                "since": "2021-06-24T00:00:20.194929+00:00",
                "until": "2023-06-24T00:00:20.194929+00:00",
            },
            {
                "where": [
                    "emission_time > {since:DateTime64(6)}",
                    "emission_time <= {until:DateTime64(6)}",
                ],
                "params": {
                    "ascending": False,
                    "attachments": False,
                    "format": "exact",
                    "limit": 0,
                    "related_activities": False,
                    "related_agents": False,
                    "since": datetime(
                        2021, 6, 24, 0, 0, 20, 194929, tzinfo=timezone.utc
                    ).isoformat(),
                    "until": datetime(
                        2023, 6, 24, 0, 0, 20, 194929, tzinfo=timezone.utc
                    ).isoformat(),
                },
                "limit": 0,
                "sort": "emission_time DESCENDING, event_id DESCENDING",
            },
        ),
        # 8. Query with pagination and pit_id.
        (
            {"search_after": "1686557542970|0", "pit_id": "46ToAwMDaWR5BXV1a"},
            {
                "where": [
                    (
                        "(emission_time < {search_after:DateTime64(6)}"
                        " OR "
                        "(emission_time = {search_after:DateTime64(6)}"
                        " AND "
                        "event_id < {pit_id:UUID}))"
                    ),
                ],
                "params": {
                    "ascending": False,
                    "attachments": False,
                    "format": "exact",
                    "limit": 0,
                    "pit_id": "46ToAwMDaWR5BXV1a",
                    "related_activities": False,
                    "related_agents": False,
                    "search_after": "1686557542970|0",
                },
                "limit": 0,
                "sort": "emission_time DESCENDING, event_id DESCENDING",
            },
        ),
    ],
)
def test_backends_database_clickhouse_query_statements_query(
    params,
    expected_params,
    monkeypatch,
    clickhouse,
    clickhouse_lrs_backend,
):
    """Test the ClickHouse backend query_statements method, given a search query
    failure, should raise a BackendException and log the error.
    """
    # pylint: disable=unused-argument

    def mock_read(query, target, ignore_errors):
        """Mock the `ClickHouseDataBackend.read` method."""

        assert query == {
            "select": ["event_id", "emission_time", "event"],
            "where": expected_params["where"],
            "parameters": expected_params["params"],
            "limit": expected_params["limit"],
            "sort": expected_params["sort"],
        }

        return {}

    backend = clickhouse_lrs_backend()
    monkeypatch.setattr(backend, "read", mock_read)
    backend.query_statements(RalphStatementsQuery.construct(**params))
    backend.close()


def test_backends_lrs_clickhouse_lrs_backend_query_statements(
    clickhouse, clickhouse_lrs_backend
):
    """Test the `ClickHouseLRSBackend.query_statements` method, given a query,
    should return matching statements.
    """
    # pylint: disable=unused-argument, invalid-name
    backend = clickhouse_lrs_backend()

    # Insert documents
    date_str = "09-19-2022"
    datetime_object = datetime.strptime(date_str, "%m-%d-%Y").utcnow()
    test_id = str(uuid.uuid4())
    statements = [
        {
            "id": test_id,
            "timestamp": datetime_object.isoformat(),
            "actor": {"account": {"name": "test_name"}},
            "verb": {"id": "verb_id"},
            "object": {"id": "http://example.com", "objectType": "Activity"},
        },
    ]

    success = backend.write(statements, chunk_size=1)
    assert success == 1

    # Check the expected search query results.
    result = backend.query_statements(
        RalphStatementsQuery.construct(statementId=test_id, limit=10)
    )
    assert result.statements == statements
    backend.close()


def test_backends_lrs_clickhouse_lrs_backend__find(clickhouse, clickhouse_lrs_backend):
    """Test the `ClickHouseLRSBackend._find` method, given a query,
    should return matching statements.
    """
    # pylint: disable=unused-argument, invalid-name
    backend = clickhouse_lrs_backend()

    # Insert documents
    date_str = "09-19-2022"
    datetime_object = datetime.strptime(date_str, "%m-%d-%Y").utcnow()
    statements = [
        {
            "id": str(uuid.uuid4()),
            "timestamp": datetime_object.isoformat(),
            "actor": {"account": {"name": "test_name"}},
            "verb": {"id": "verb_id"},
            "object": {"id": "http://example.com", "objectType": "Activity"},
        },
    ]

    success = backend.write(statements, chunk_size=1)
    assert success == 1

    # Check the expected search query results.
    result = backend.query_statements(RalphStatementsQuery.construct())
    assert result.statements == statements
    backend.close()


def test_backends_lrs_clickhouse_lrs_backend_query_statements_by_ids(
    clickhouse, clickhouse_lrs_backend
):
    """Test the `ClickHouseLRSBackend.query_statements_by_ids` method, given
    a list of ids, should return matching statements.
    """
    # pylint: disable=unused-argument
    backend = clickhouse_lrs_backend()

    # Insert documents
    date_str = "09-19-2022"
    datetime_object = datetime.strptime(date_str, "%m-%d-%Y").utcnow()
    test_id = str(uuid.uuid4())
    statements = [
        {
            "id": test_id,
            "timestamp": datetime_object.isoformat(),
            "actor": {"account": {"name": "test_name"}},
            "verb": {"id": "verb_id"},
            "object": {"id": "http://example.com", "objectType": "Activity"},
        },
    ]

    count = backend.write(statements, chunk_size=1)
    assert count == 1

    # Check the expected search query results.
    result = list(backend.query_statements_by_ids([test_id]))
    assert result[0] == statements[0]
    backend.close()


def test_backends_lrs_clickhouse_lrs_backend_query_statements_client_failure(
    clickhouse, clickhouse_lrs_backend, monkeypatch, caplog
):
    """Test the `ClickHouseLRSBackend.query_statements`, given a client query
    failure, should raise a `BackendException` and log the error.
    """
    # pylint: disable=invalid-name,unused-argument

    def mock_query(*args, **kwargs):
        """Mock the clickhouse_connect.client.search method."""
        raise ClickHouseError("Query error")

    backend = clickhouse_lrs_backend()
    monkeypatch.setattr(backend.client, "query", mock_query)

    caplog.set_level(logging.ERROR)

    msg = "Failed to read documents: Query error"
    with pytest.raises(BackendException, match=msg):
        next(backend.query_statements(RalphStatementsQuery.construct()))

    assert (
        "ralph.backends.lrs.clickhouse",
        logging.ERROR,
        "Failed to read from ClickHouse",
    ) in caplog.record_tuples
    backend.close()


def test_backends_lrs_clickhouse_lrs_backend_query_statements_by_ids_client_failure(
    clickhouse, clickhouse_lrs_backend, monkeypatch, caplog
):
    """Test the `ClickHouseLRSBackend.query_statements_by_ids`, given a client
    query failure, should raise a `BackendException` and log the error.
    """
    # pylint: disable=invalid-name,unused-argument

    def mock_query(*args, **kwargs):
        """Mock the clickhouse_connect.client.search method."""
        raise ClickHouseError("Query error")

    backend = clickhouse_lrs_backend()
    monkeypatch.setattr(backend.client, "query", mock_query)

    caplog.set_level(logging.ERROR)

    msg = "Failed to read documents: Query error"
    with pytest.raises(BackendException, match=msg):
        next(backend.query_statements_by_ids(["test_id"]))

    assert (
        "ralph.backends.lrs.clickhouse",
        logging.ERROR,
        "Failed to read from ClickHouse",
    ) in caplog.record_tuples
    backend.close()
