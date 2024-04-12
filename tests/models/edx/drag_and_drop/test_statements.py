"""Tests for the drag and drop event models."""

import json

import pytest

from ralph.models.edx.drag_and_drop.statements import (
    EdxDragAndDropV2FeedbackClosed,
    EdxDragAndDropV2FeedbackOpened,
    EdxDragAndDropV2ItemDropped,
    EdxDragAndDropV2ItemPickedUp,
    EdxDragAndDropV2Loaded,
)
from ralph.models.selector import ModelSelector

from tests.factories import mock_instance


@pytest.mark.parametrize(
    "class_",
    [
        EdxDragAndDropV2FeedbackClosed,
        EdxDragAndDropV2FeedbackOpened,
        EdxDragAndDropV2ItemDropped,
        EdxDragAndDropV2ItemPickedUp,
        EdxDragAndDropV2Loaded,
    ],
)
def test_models_edx_drag_and_drop_selectors_with_valid_statements(class_):
    """Test given a valid drag and drop edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(mock_instance(class_).model_dump_json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


def test_models_edx_edx_drag_and_drop_v2_feedback_closed_with_valid_statement():
    """Test that a `edx.drag_and_drop_v2.feedback.closed` statement has the expected
    `event_type` and `name`."""
    statement = mock_instance(EdxDragAndDropV2FeedbackClosed)
    assert statement.event_type == "edx.drag_and_drop_v2.feedback.closed"
    assert statement.name == "edx.drag_and_drop_v2.feedback.closed"


def test_models_edx_edx_drag_and_drop_v2_feedback_opened_with_valid_statement():
    """Test that a `edx.drag_and_drop_v2.feedback.opened` statement has the expected
    `event_type` and `name`."""
    statement = mock_instance(EdxDragAndDropV2FeedbackOpened)
    assert statement.event_type == "edx.drag_and_drop_v2.feedback.opened"
    assert statement.name == "edx.drag_and_drop_v2.feedback.opened"


def test_models_edx_edx_drag_and_drop_v2_item_dropped_with_valid_statement():
    """Test that a `edx.drag_and_drop_v2.item.dropped` statement has the expected
    `event_type` and `name`."""
    statement = mock_instance(EdxDragAndDropV2ItemDropped)
    assert statement.event_type == "edx.drag_and_drop_v2.item.dropped"
    assert statement.name == "edx.drag_and_drop_v2.item.dropped"


def test_models_edx_edx_drag_and_drop_v2_item_picked_up_with_valid_statement():
    """Test that a `edx.drag_and_drop_v2.item.picked_up` statement has the expected
    `event_type` and `name`."""
    statement = mock_instance(EdxDragAndDropV2ItemPickedUp)
    assert statement.event_type == "edx.drag_and_drop_v2.item.picked_up"
    assert statement.name == "edx.drag_and_drop_v2.item.picked_up"


def test_models_edx_edx_drag_and_drop_v2_loaded_with_valid_statement():
    """Test that a `edx.drag_and_drop_v2.loaded` statement has the expected
    `event_type` and `name`."""
    statement = mock_instance(EdxDragAndDropV2Loaded)
    assert statement.event_type == "edx.drag_and_drop_v2.loaded"
    assert statement.name == "edx.drag_and_drop_v2.loaded"
