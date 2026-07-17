"""Unit tests for ralph.api.partial_success."""

import pytest
from pydantic import ValidationError

from ralph.api.models import LaxStatement
from ralph.api.partial_success import (
    partition_statements,
    partial_success_enabled,
    validate_strict_statements,
)
from ralph.backends.lrs import es_key_validation

from ..helpers import mock_statement


def test_partition_statements_splits_valid_and_invalid():
    good_a = mock_statement()
    good_b = mock_statement()
    bad = {"verb": {"id": "http://example.com/verb"}, "object": {"id": "http://ex.com/o"}}

    valid, errors = partition_statements([good_a, bad, good_b])

    assert len(valid) == 2
    assert valid[0][0] == 0
    assert valid[1][0] == 2
    assert len(errors) == 1
    assert errors[0].index == 1
    assert "actor" in errors[0].reason


def test_validate_strict_statements_raises_on_invalid():
    with pytest.raises(Exception) as exc_info:
        validate_strict_statements([mock_statement(), {}])
    assert exc_info.value.status_code == 422


@pytest.mark.parametrize(
    "partial_success, ignore_invalid, default_enabled, expected",
    [
        (None, False, False, False),
        (None, False, True, True),
        (True, False, False, True),
        (False, False, True, False),
        (None, True, False, True),
    ],
)
def test_partial_success_enabled(partial_success, ignore_invalid, default_enabled, expected):
    assert (
        partial_success_enabled(
            partial_success=partial_success,
            ignore_invalid=ignore_invalid,
            default_enabled=default_enabled,
        )
        is expected
    )


@pytest.fixture
def es_key_validation_enabled(monkeypatch):
    monkeypatch.setattr(es_key_validation.settings, "RUNSERVER_BACKEND", "es")
    monkeypatch.setattr(es_key_validation.settings, "LRS_ELASTICSEARCH_VALIDATE_KEYS", True)


def test_partition_statements_rejects_elasticsearch_incompatible_keys(
    es_key_validation_enabled,
):
    good = mock_statement()
    bad_empty_key = {
        **mock_statement(),
        "context": {
            "extensions": {
                "http://example.com/quiz": {"": "match"},
            }
        },
    }
    bad_dot_key = {
        **mock_statement(),
        "context": {
            "extensions": {
                "http://example.com/quiz": {"nested.key": 1},
            }
        },
    }

    valid, errors = partition_statements([good, bad_empty_key, bad_dot_key])

    assert len(valid) == 1
    assert valid[0][0] == 0
    assert len(errors) == 2
    assert errors[0].index == 1
    assert "empty string" in errors[0].reason
    assert errors[1].index == 2
    assert "nested.key" in errors[1].reason


def test_validate_strict_statements_rejects_elasticsearch_incompatible_keys(
    es_key_validation_enabled,
):
    bad = {
        **mock_statement(),
        "context": {
            "extensions": {
                "http://example.com/quiz": {"": "match"},
            }
        },
    }

    with pytest.raises(Exception) as exc_info:
        validate_strict_statements([mock_statement(), bad])

    assert exc_info.value.status_code == 422
    assert "empty string" in str(exc_info.value.detail)
