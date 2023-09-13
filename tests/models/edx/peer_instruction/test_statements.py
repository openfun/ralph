"""Tests for the peer_instruction event models."""

import json

import pytest
from hypothesis import strategies as st

from ralph.models.edx.peer_instruction.statements import (
    PeerInstructionAccessed,
    PeerInstructionOriginalSubmitted,
    PeerInstructionRevisedSubmitted,
)
from ralph.models.selector import ModelSelector

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


@pytest.mark.parametrize(
    "class_",
    [
        PeerInstructionAccessed,
        PeerInstructionOriginalSubmitted,
        PeerInstructionRevisedSubmitted,
    ],
)
@custom_given(st.data())
def test_models_edx_peer_instruction_selectors_with_valid_statements(class_, data):
    """Test given a valid peer_instruction edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(data.draw(custom_builds(class_)).json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


@custom_given(PeerInstructionAccessed)
def test_models_edx_peer_instruction_accessed_with_valid_statement(
    statement,
):
    """Test that a `ubc.peer_instruction.accessed` statement has the expected
    `event_type`."""
    assert statement.event_type == "ubc.peer_instruction.accessed"
    assert statement.name == "ubc.peer_instruction.accessed"


@custom_given(PeerInstructionOriginalSubmitted)
def test_models_edx_peer_instruction_original_submitted_with_valid_statement(
    statement,
):
    """Test that a `ubc.peer_instruction.original_submitted` statement has the
    expected `event_type`."""
    assert statement.event_type == "ubc.peer_instruction.original_submitted"
    assert statement.name == "ubc.peer_instruction.original_submitted"


@custom_given(PeerInstructionRevisedSubmitted)
def test_models_edx_peer_instruction_revised_submitted_with_valid_statement(
    statement,
):
    """Test that a `ubc.peer_instruction.revised_submitted` statement has the
    expected `event_type`."""
    assert statement.event_type == "ubc.peer_instruction.revised_submitted"
    assert statement.name == "ubc.peer_instruction.revised_submitted"
