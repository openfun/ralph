"""Tests for test helpers."""

from uuid import uuid4

import pytest

from .helpers import (
    assert_statement_get_responses_are_equivalent,
    string_is_date,
    string_is_uuid,
)


def test_helpers_string_is_date():
    """Test that strings representing dates are properly identified."""
    string = "2022-06-22T08:31:38+00:00"
    assert string_is_date(string)

    string = "a2023-06-22T08:31:38+00:00"
    assert not string_is_date(string)


def test_helpers_string_is_uuid():
    """Test that strings representing uuids are properly identified."""
    string = str(uuid4())
    assert string_is_uuid(string)

    string = "not_a_valid_uuid"
    assert not string_is_uuid(string)


@pytest.mark.parametrize(
    "modified_fields,are_equivalent",
    [
        (
            {
                "timestamp": None,
                "version": None,
                "authority": "authority_2",
                "stored": "stored_2",
            },
            True,
        ),
        ({"actor": {"actor_field": "actor_2"}}, False),
        ({"verb": "verb_2"}, False),
        ({"object": "object_2"}, False),
        ({"id": "id_2"}, False),
        ({"result": "result_2"}, False),
        ({"context": "context_2"}, False),
        ({"attachments": "attachments_2"}, False),
        ({"timestamp": "timestamp_2"}, False),
        ({"version": "version_2"}, False),
    ],
)
def test_helpers_assert_statement_get_responses_are_equivalent(
    modified_fields, are_equivalent
):
    """Test the equivalency assertion for get responses.

    Equivalency (term NOT in specification) means that two statements have
    identical values on all fields except `authority`, `stored` and `timestamp`
    (where the value may or may not be identical).
    """
    statement_1 = {
        "actor": {"actor_field": "actor_1"},
        "verb": "verb_1",
        "object": "object_1",
        "id": "id_1",
        "result": "result_1",
        "context": "context_1",
        "attachments": "attachments_1",
        "authority": "authority_1",
        "stored": "stored_1",
        "timestamp": "timestamp_1",
        "version": "version_1",
    }

    # Statement to compare to
    statement_2 = statement_1.copy()
    statement_2.update(modified_fields)
    statement_2 = {key: value for key, value in statement_2.items() if value}

    get_response_1 = {"statements": [statement_1]}
    get_response_2 = {"statements": [statement_2]}

    if are_equivalent:
        assert_statement_get_responses_are_equivalent(get_response_1, get_response_2)
        assert_statement_get_responses_are_equivalent(get_response_2, get_response_1)
    else:
        with pytest.raises(AssertionError, match="are not equivalent"):
            assert_statement_get_responses_are_equivalent(
                get_response_1, get_response_2
            )
        with pytest.raises(AssertionError, match="are not equivalent"):
            assert_statement_get_responses_are_equivalent(
                get_response_2, get_response_1
            )


def test_helpers_assert_statement_get_responses_are_equivalent_length_error():
    """Test that responses with different numbers of statements return an error."""

    statement = {
        "actor": {"actor_field": "actor_1"},
        "verb": "verb_1",
        "object": "object_1",
        "id": "id_1",
        "result": "result_1",
        "context": "context_1",
        "attachments": "attachments_1",
        "authority": "authority_1",
        "stored": "stored_1",
        "timestamp": "timestamp_1",
        "version": "version_1",
    }

    get_response_1 = {"statements": [statement]}
    get_response_2 = {"statements": [statement, statement]}

    with pytest.raises(AssertionError):
        assert_statement_get_responses_are_equivalent(get_response_1, get_response_2)
    with pytest.raises(AssertionError):
        assert_statement_get_responses_are_equivalent(get_response_2, get_response_1)
