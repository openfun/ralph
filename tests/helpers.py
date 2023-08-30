"""Utilities for testing Ralph."""
import datetime
import uuid

from ralph.utils import statements_are_equivalent


def string_is_date(string: str):
    """Check if string can be parsed as a date."""
    try:
        datetime.datetime.fromisoformat(string)
        return True
    except ValueError:
        return False


def string_is_uuid(string: str):
    """Check if string is a valid uuid."""
    try:
        uuid.UUID(string)
        return True
    except ValueError:
        return False


def assert_statement_get_responses_are_equivalent(response_1: dict, response_2: dict):
    """Check that responses to GET /statements are equivalent.

    Check that all statements in response are equivalent, meaning that all
    fields not modified by the LRS are equal.
    """

    assert response_1.keys() == response_2.keys()

    def _all_but_statements(response):
        return {key: val for key, val in response.items() if key != "statements"}

    assert _all_but_statements(response_1) == _all_but_statements(response_2)

    # Assert the statements part of the response is equivalent
    assert "statements" in response_1.keys()
    assert "statements" in response_2.keys()
    assert len(response_1["statements"]) == len(response_2["statements"])

    for statement_1, statement_2 in zip(
        response_1["statements"], response_2["statements"]
    ):
        assert statements_are_equivalent(
            statement_1, statement_2
        ), "Statements in get responses are not equivalent, or not in the same order."
