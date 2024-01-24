"""Tests for the peer_instruction event models."""

import json

import pytest

from ralph.models.edx.peer_instruction.statements import (
    PeerInstructionAccessed,
    PeerInstructionOriginalSubmitted,
    PeerInstructionRevisedSubmitted,
)
from ralph.models.selector import ModelSelector

from tests.factories import mock_instance


@pytest.mark.parametrize(
    "class_",
    [
        PeerInstructionAccessed,
        PeerInstructionOriginalSubmitted,
        PeerInstructionRevisedSubmitted,
    ],
)
def test_models_edx_peer_instruction_selectors_with_valid_statements(class_):
    """Test given a valid peer_instruction edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(mock_instance(class_).model_dump_json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


def test_models_edx_peer_instruction_accessed_with_valid_statement():
    """Test that a `ubc.peer_instruction.accessed` statement has the expected
    `event_type`.
    """
    statement = mock_instance(PeerInstructionAccessed)
    assert statement.event_type == "ubc.peer_instruction.accessed"
    assert statement.name == "ubc.peer_instruction.accessed"


def test_models_edx_peer_instruction_original_submitted_with_valid_statement():
    """Test that a `ubc.peer_instruction.original_submitted` statement has the
    expected `event_type`.
    """
    statement = mock_instance(PeerInstructionOriginalSubmitted)
    assert statement.event_type == "ubc.peer_instruction.original_submitted"
    assert statement.name == "ubc.peer_instruction.original_submitted"


def test_models_edx_peer_instruction_revised_submitted_with_valid_statement():
    """Test that a `ubc.peer_instruction.revised_submitted` statement has the
    expected `event_type`.
    """
    statement = mock_instance(PeerInstructionRevisedSubmitted)
    assert statement.event_type == "ubc.peer_instruction.revised_submitted"
    assert statement.name == "ubc.peer_instruction.revised_submitted"
