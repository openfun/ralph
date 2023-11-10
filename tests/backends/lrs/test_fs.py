"""Tests for Ralph FileSystem LRS backend."""

import pytest

from ralph.backends.lrs.base import RalphStatementsQuery
from ralph.backends.lrs.fs import FSLRSBackend


def test_backends_lrs_fs_default_instantiation(monkeypatch, fs):
    """Test the `FSLRSBackend` default instantiation."""
    fs.create_file(".env")
    monkeypatch.delenv("RALPH_BACKENDS__LRS__FS__DEFAULT_LRS_FILE", raising=False)
    backend = FSLRSBackend()
    assert backend.settings.DEFAULT_LRS_FILE == "fs_lrs.jsonl"

    monkeypatch.setenv("RALPH_BACKENDS__LRS__FS__DEFAULT_LRS_FILE", "foo.txt")
    backend = FSLRSBackend()
    assert backend.settings.DEFAULT_LRS_FILE == "foo.txt"


@pytest.mark.parametrize(
    "params,expected_statement_ids",
    [
        # 0. Default query.
        ({}, ["0", "1", "2", "3", "4", "5", "6", "7", "8"]),
        # 1. Query by statementId.
        ({"statementId": "1"}, ["1"]),
        # 2. Query by statementId and agent with mbox IFI.
        ({"statementId": "1", "agent": {"mbox": "mailto:foo@bar.baz"}}, ["1"]),
        # 3. Query by statementId and agent with mbox IFI (no match).
        ({"statementId": "1", "agent": {"mbox": "mailto:bar@bar.baz"}}, []),
        # 4. Query by statementId and agent with mbox_sha1sum IFI.
        ({"statementId": "0", "agent": {"mbox_sha1sum": "foo_sha1sum"}}, ["0"]),
        # 5. Query by agent with mbox_sha1sum IFI (no match).
        ({"statementId": "0", "agent": {"mbox_sha1sum": "bar_sha1sum"}}, []),
        # 6. Query by statementId and agent with openid IFI.
        ({"statementId": "2", "agent": {"openid": "foo_openid"}}, ["2"]),
        # 7. Query by statementId and agent with openid IFI (no match).
        ({"statementId": "2", "agent": {"openid": "bar_openid"}}, []),
        # 8. Query by statementId and agent with account IFI.
        (
            {
                "statementId": "3",
                "agent": {
                    "account__home_page": "foo_home",
                    "account__name": "foo_name",
                },
            },
            ["3"],
        ),
        # 9. Query by statementId and agent with account IFI (no match).
        (
            {
                "statementId": "3",
                "agent": {
                    "account__home_page": "foo_home",
                    "account__name": "bar_name",
                },
            },
            [],
        ),
        # 10. Query by verb and activity.
        ({"verb": "foo_verb", "activity": "foo_object"}, ["1", "2"]),
        # 11. Query by timerange (with since/until).
        (
            {
                "since": "2021-06-24T00:00:20.194929+00:00",
                "until": "2023-06-24T00:00:20.194929+00:00",
            },
            ["1", "3"],
        ),
        # 12. Query by timerange (with until).
        (
            {
                "until": "2023-06-24T00:00:20.194929+00:00",
            },
            ["0", "1", "3"],
        ),
        # 13. Query with pagination.
        ({"search_after": "1"}, ["2", "3", "4", "5", "6", "7", "8"]),
        # 14. Query with pagination and limit.
        ({"search_after": "1", "limit": 2}, ["2", "3"]),
        # 15. Query with pagination and limit.
        ({"search_after": "3", "limit": 5}, ["4", "5", "6", "7", "8"]),
        # 16. Query in ascending order.
        ({"ascending": True}, ["8", "7", "6", "5", "4", "3", "2", "1", "0"]),
        # 17. Query by registration.
        ({"registration": "b0d0e57d-9fbf-42e3-ba60-85e0be6f709d"}, ["2", "4"]),
        # 18. Query by activity without related activities.
        ({"activity": "bar_object", "related_activities": False}, ["0"]),
        # 19. Query by activity with related activities.
        (
            {"activity": "bar_object", "related_activities": True},
            ["0", "1", "2", "4", "5"],
        ),
        # 20. Query by related agent with mbox IFI.
        (
            {"agent": {"mbox": "mailto:foo@bar.baz"}, "related_agents": True},
            ["1", "3", "4", "5", "6", "7"],
        ),
        # 21. Query by related agent with mbox_sha1sum IFI.
        (
            {"agent": {"mbox_sha1sum": "foo_sha1sum"}, "related_agents": True},
            ["0", "1", "2", "5", "6", "7", "8"],
        ),
        # 22. Query by related agent with openid IFI.
        (
            {"agent": {"openid": "foo_openid"}, "related_agents": True},
            ["0", "2", "4", "5", "6", "7"],
        ),
        # 23. Query by related agent with account IFI.
        (
            {
                "agent": {
                    "account__home_page": "foo_home",
                    "account__name": "foo_name",
                },
                "related_agents": True,
            },
            ["1", "2", "3", "4", "5", "7"],
        ),
        # 24. Query by authority with mbox IFI.
        ({"authority": {"mbox": "mailto:foo@bar.baz"}}, ["4"]),
        # 25. Query by authority with mbox IFI (no match).
        ({"authority": {"mbox": "mailto:bar@bar.baz"}}, []),
        # 26. Query by authority with mbox_sha1sum IFI.
        ({"authority": {"mbox_sha1sum": "foo_sha1sum"}}, ["7"]),
        # 27. Query by authority with mbox_sha1sum IFI (no match).
        ({"authority": {"mbox_sha1sum": "bar_sha1sum"}}, []),
        # 28. Query by authority with openid IFI.
        ({"authority": {"openid": "foo_openid"}}, ["6"]),
        # 29. Query by authority with openid IFI (no match).
        ({"authority": {"openid": "bar_openid"}}, []),
        # 30. Query by authority with account IFI.
        (
            {
                "authority": {
                    "account__home_page": "foo_home",
                    "account__name": "foo_name",
                },
            },
            ["2"],
        ),
        # 31. Query by authority with account IFI (no match).
        (
            {
                "authority": {
                    "account__home_page": "foo_home",
                    "account__name": "bar_name",
                },
            },
            [],
        ),
    ],
)
def test_backends_lrs_fs_query_statements_query(
    params, expected_statement_ids, fs_lrs_backend
):
    """Test the `FSLRSBackend.query_statements` method, given valid statement
    parameters, should return the expected statements.
    """
    statements = [
        {
            "id": "0",
            "actor": {"mbox_sha1sum": "foo_sha1sum"},
            "verb": {"id": "foo_verb"},
            "object": {"id": "bar_object", "objectType": "Activity"},
            "context": {
                "registration": "de867099-77ee-453b-949e-2c1933734436",
                "instructor": {"mbox": "mailto:bar@bar.baz"},
                "team": {"openid": "foo_openid"},
            },
            "timestamp": "2021-06-24T00:00:20.194929+00:00",
        },
        {
            "id": "1",
            "actor": {"mbox": "mailto:foo@bar.baz"},
            "verb": {"id": "foo_verb"},
            "object": {
                "id": "foo_object",
                "account": {"name": "foo_name", "homePage": "foo_home"},
            },
            "context": {
                "instructor": {"mbox_sha1sum": "foo_sha1sum"},
                "contextActivities": {"parent": {"id": "bar_object"}},
            },
            "timestamp": "2021-06-24T00:00:20.194930+00:00",
        },
        {
            "id": "2",
            "actor": {"openid": "foo_openid"},
            "verb": {"id": "foo_verb"},
            "object": {"id": "foo_object", "objectType": "Activity"},
            "context": {
                "registration": "b0d0e57d-9fbf-42e3-ba60-85e0be6f709d",
                "contextActivities": {"grouping": [{"id": "bar_object"}]},
                "team": {"mbox_sha1sum": "foo_sha1sum"},
            },
            "timestamp": "UNPARSABLE-2022-06-24T00:00:20.194929+00:00",
            "authority": {"account": {"name": "foo_name", "homePage": "foo_home"}},
        },
        {
            "id": "3",
            "actor": {"account": {"name": "foo_name", "homePage": "foo_home"}},
            "verb": {"id": "bar_verb"},
            "object": {"objectType": "Agent", "mbox": "mailto:foo@bar.baz"},
            "timestamp": "2023-06-24T00:00:20.194929+00:00",
        },
        {
            "id": "4",
            "verb": {"id": "bar_verb"},
            "object": {"id": "foo_object"},
            "context": {
                "registration": "b0d0e57d-9fbf-42e3-ba60-85e0be6f709d",
                "contextActivities": {
                    "category": [{"id": "foo_object"}, {"id": "baz_object"}],
                    "other": [{"id": "bar_object"}, {"id": "baz_object"}],
                },
                "instructor": {"openid": "foo_openid"},
                "team": {"account": {"name": "foo_name", "homePage": "foo_home"}},
            },
            "timestamp": "2024-06-24T00:00:20.194929+00:00",
            "authority": {"mbox": "mailto:foo@bar.baz"},
        },
        {
            "id": "5",
            "actor": {
                "mbox_sha1sum": "foo_sha1sum",
            },
            "verb": {"id": "qux_verb"},
            "object": {
                "objectType": "SubStatement",
                "actor": {"openid": "foo_openid"},
                "verb": {"id": "bar_verb"},
                "object": {"id": "bar_object", "objectType": "Activity"},
                "context": {
                    "instructor": {
                        "account": {"name": "foo_name", "homePage": "foo_home"}
                    },
                    "team": {
                        "mbox": "mailto:foo@bar.baz",
                    },
                },
            },
        },
        {
            "id": "6",
            "object": {
                "objectType": "Agent",
                "mbox_sha1sum": "foo_sha1sum",
            },
            "context": {"instructor": {"mbox": "mailto:foo@bar.baz"}},
            "authority": {"openid": "foo_openid"},
        },
        {
            "id": "7",
            "object": {"objectType": "Agent", "openid": "foo_openid"},
            "context": {
                "instructor": {"account": {"name": "foo_name", "homePage": "foo_home"}},
                "team": {
                    "mbox": "mailto:foo@bar.baz",
                },
            },
            "authority": {"mbox_sha1sum": "foo_sha1sum"},
        },
        {
            "id": "8",
            "object": {
                "objectType": "SubStatement",
                "actor": {"mbox_sha1sum": "foo_sha1sum"},
            },
        },
    ]
    backend = fs_lrs_backend()
    backend.write(statements)
    result = backend.query_statements(RalphStatementsQuery.construct(**params))
    ids = [statement.get("id") for statement in result.statements]
    assert ids == expected_statement_ids


def test_backends_lrs_fs_query_statements_by_ids(fs_lrs_backend):
    """Test the `FSLRSBackend.query_statements_by_ids` method, given a valid search
    query, should return the expected results.
    """
    backend = fs_lrs_backend()
    assert not backend.query_statements_by_ids(["foo"])
    backend.write(
        [
            {"id": "foo"},
            {"id": "bar"},
            {"id": "baz"},
        ]
    )
    assert not backend.query_statements_by_ids([])
    assert not backend.query_statements_by_ids(["qux", "foobar"])
    assert backend.query_statements_by_ids(["foo"]) == [{"id": "foo"}]
    assert backend.query_statements_by_ids(["bar", "baz"]) == [
        {"id": "bar"},
        {"id": "baz"},
    ]
