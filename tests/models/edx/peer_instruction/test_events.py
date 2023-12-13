"""Tests for peer instruction models event fields."""

import json

import pytest
from pydantic.error_wrappers import ValidationError

from ralph.models.edx.peer_instruction.fields.events import PeerInstructionEventField

# from tests.fixtures.hypothesis_strategies import custom_given
from tests.factories import mock_instance


def test_models_edx_peer_instruction_event_field_with_valid_field():
    """Test that a valid `PeerInstructionEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(PeerInstructionEventField)
    assert len(field.rationale) <= 12500


def test_models_edx_peer_instruction_event_field_with_invalid_rationale():
    """Test that a valid `PeerInstructionEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(PeerInstructionEventField)

    invalid_field = json.loads(field.json())
    invalid_field["rationale"] = "x" * 12501
    with pytest.raises(
        ValidationError,
        match="rationale\n  ensure this value has at most 12500 characters",
    ):
        PeerInstructionEventField(**invalid_field)
