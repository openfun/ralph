"""Tests for the browser event models."""

import json
import re

import pytest
from pydantic.error_wrappers import ValidationError

from ralph.models.edx.browser import BaseBrowserModel

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(BaseBrowserModel)
def test_models_edx_base_browser_model_with_valid_statement(statement):
    """Tests that a valid base browser statement does not raise a `ValidationError`."""

    assert re.match(r"^[a-f0-9]{32}$", statement.session) or statement.session == ""


@pytest.mark.parametrize(
    "session,error",
    [
        # less than 32 characters
        ("abcdef0123456789", "session\n  string does not match regex"),
        # more than 32 characters
        ("abcdef0123456789abcdef0123456789abcdef", "string does not match regex"),
        # with excluded characters
        ("abcdef0123456789_abcdef012345678", "string does not match regex"),
    ],
)
@custom_given(BaseBrowserModel)
def test_models_edx_base_browser_model_with_invalid_statement(
    session, error, statement
):
    """Tests that a invalid base browser statement raises a `ValidationError`."""

    invalid_statement = json.loads(statement.json())
    invalid_statement["session"] = session

    with pytest.raises(ValidationError, match=error):
        BaseBrowserModel(**invalid_statement)
