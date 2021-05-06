"""Tests for the xAPI context fields"""

import pytest
from pydantic import ValidationError

from ralph.models.xapi.constants import XAPI_EXTENSION_AGENT, XAPI_EXTENSION_SESSION
from ralph.models.xapi.fields.context import ContextExtensionsField


def test_models_xapi_fields_context_context_field_with_valid_session():
    """Tests that a valid context field does not raise ValidationErrors."""

    try:
        ContextExtensionsField(
            **{XAPI_EXTENSION_SESSION: "abcdef0123456789abcdef0123456789"}
        )
    except ValidationError as err:
        pytest.fail("Valid context field should not raise ValidationErrors: %s" % err)


@pytest.mark.parametrize(
    "value,error",
    [
        # less than 32 characters
        ("abcdef0123456789", "does not match regex"),
        # more than 32 characters
        ("abcdef0123456789abcdef0123456789abcdef", "does not match regex"),
        # with excluded characters
        ("abcdef0123456789_abcdef012345678", "does not match regex"),
    ],
)
def test_models_xapi_fields_context_context_field_with_invalid_session(value, error):
    """Tests that a invalid context field raises ValidationErrors."""

    with pytest.raises(ValidationError, match=error):
        ContextExtensionsField(**{XAPI_EXTENSION_SESSION: value})


def test_models_xapi_fields_context_context_field_with_invalid_agent():
    """Tests that a invalid context field raises ValidationErrors."""

    with pytest.raises(ValidationError, match="value has at least 1 characters"):
        ContextExtensionsField(**{XAPI_EXTENSION_AGENT: ""})
