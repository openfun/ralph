"""Unit tests for ralph.api.partial_success."""

import pytest
from pydantic import ValidationError

from ralph.api.models import LaxStatement
from ralph.api.partial_success import partition_statements, validate_strict_statements

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
