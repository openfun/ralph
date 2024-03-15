"""Tests for the peer_instruction event models."""

import json

import pytest
from hypothesis import strategies as st

from ralph.models.edx.content_library_interaction.statements import (
    EdxLibraryContentBlockContentAssigned,
    EdxLibraryContentBlockContentRemoved,
)
from ralph.models.selector import ModelSelector

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


@pytest.mark.parametrize(
    "class_",
    [EdxLibraryContentBlockContentAssigned, EdxLibraryContentBlockContentRemoved],
)
@custom_given(st.data())
def test_models_edx_content_library_interaction_selectors_with_valid_statements(
    class_, data
):
    """Test given a valid content library interaction edX statement the
    `get_first_model` selector method should return the expected model.
    """
    statement = json.loads(data.draw(custom_builds(class_)).json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


@custom_given(EdxLibraryContentBlockContentAssigned)
def test_models_edx_edx_library_content_block_content_assigned_with_valid_statement(
    statement,
):
    """Test that a `edx.librarycontentblock.content.assigned` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.librarycontentblock.content.assigned"
    assert statement.name == "edx.librarycontentblock.content.assigned"


@custom_given(EdxLibraryContentBlockContentRemoved)
def test_models_edx_edx_library_content_block_content_removed_with_valid_statement(
    statement,
):
    """Test that a `edx.librarycontentblock.content.removed` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.librarycontentblock.content.removed"
    assert statement.name == "edx.librarycontentblock.content.removed"
