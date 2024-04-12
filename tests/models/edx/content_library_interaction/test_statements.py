"""Tests for the peer_instruction event models."""

import json

import pytest

from ralph.models.edx.content_library_interaction.statements import (
    EdxLibraryContentBlockContentAssigned,
    EdxLibraryContentBlockContentRemoved,
)
from ralph.models.selector import ModelSelector

from tests.factories import mock_instance


@pytest.mark.parametrize(
    "class_",
    [EdxLibraryContentBlockContentAssigned, EdxLibraryContentBlockContentRemoved],
)
def test_models_edx_content_library_interaction_selectors_with_valid_statements(class_):
    """Test given a valid content library interaction edX statement the
    `get_first_model` selector method should return the expected model.
    """
    statement = json.loads(mock_instance(class_).model_dump_json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


def test_models_edx_edx_library_content_block_content_assigned_with_valid_statement():
    """Test that a `edx.librarycontentblock.content.assigned` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxLibraryContentBlockContentAssigned)
    assert statement.event_type == "edx.librarycontentblock.content.assigned"
    assert statement.name == "edx.librarycontentblock.content.assigned"


def test_models_edx_edx_library_content_block_content_removed_with_valid_statement():
    """Test that a `edx.librarycontentblock.content.removed` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxLibraryContentBlockContentRemoved)
    assert statement.event_type == "edx.librarycontentblock.content.removed"
    assert statement.name == "edx.librarycontentblock.content.removed"
