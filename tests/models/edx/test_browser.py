"""Tests for the browser event models."""

import json
import re

import pytest
from pydantic import ValidationError

from ralph.models.edx.browser import BaseBrowserModel

from tests.factories import mock_instance


def test_models_edx_base_browser_model_with_valid_statement():
    """Test that a valid base browser statement does not raise a `ValidationError`."""
    statement = mock_instance(BaseBrowserModel)
    assert re.match(r"^[a-f0-9]{32}$", statement.session) or statement.session == ""


@pytest.mark.parametrize(
    "session,error",
    [
        # less than 32 characters
        ("abcdef0123456789", "String should match pattern"),
        # more than 32 characters
        ("abcdef0123456789abcdef0123456789abcdef", "String should match pattern"),
        # with excluded characters
        ("abcdef0123456789_abcdef012345678", "String should match pattern"),
    ],
)
def test_models_edx_base_browser_model_with_invalid_statement(session, error):
    """Test that an invalid base browser statement raises a `ValidationError`."""
    statement = mock_instance(BaseBrowserModel)
    invalid_statement = json.loads(statement.model_dump_json())
    invalid_statement["session"] = session

    with pytest.raises(ValidationError, match=error):
        BaseBrowserModel(**invalid_statement)
