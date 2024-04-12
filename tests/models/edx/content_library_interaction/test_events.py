"""Tests for content library interaction models event fields."""

import json

import pytest
from pydantic.error_wrappers import ValidationError

from ralph.models.edx.content_library_interaction.fields.events import (
    EdxLibraryContentBlockContentRemovedEventField,
)

from tests.factories import mock_instance


def test_models_edx_edx_library_content_block_content_removed_event_field_with_valid_field():  # noqa: E501
    """Test that a valid `EdxLibraryContentBlockContentRemovedEventField` does
    not raise a `ValidationError`.
    """
    field = mock_instance(EdxLibraryContentBlockContentRemovedEventField)
    assert field.reason in ("overlimit", "invalid")


@pytest.mark.parametrize(
    "reason",
    ["over_limit", "underlimit", "valid", "invalide"],
)
def test_models_edx_edx_library_content_block_content_removed_event_field_with_invalid_reason_value(  # noqa: E501
    reason,
):
    """Test that invalid `ORAAssessEventField` raises a `ValidationError`."""
    field = mock_instance(EdxLibraryContentBlockContentRemovedEventField)

    invalid_field = json.loads(field.json())
    invalid_field["reason"] = reason

    with pytest.raises(ValidationError, match="reason"):
        EdxLibraryContentBlockContentRemovedEventField(**invalid_field)
