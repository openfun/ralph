"""Tests for the Course Content Completion event models."""

import json

import pytest

from ralph.models.edx.course_content_completion.statements import (
    EdxDoneToggled,
    UIEdxDoneToggled,
)
from ralph.models.selector import ModelSelector

from tests.factories import mock_instance


@pytest.mark.parametrize(
    "class_",
    [EdxDoneToggled, UIEdxDoneToggled],
)
def test_models_edx_course_content_completion_selectors_with_valid_statements(class_):
    """Test given a valid course content completion edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(mock_instance(class_).model_dump_json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


def test_models_edx_edx_done_toggled_with_valid_statement():
    """Test that a `edx.done.toggled` server statement has the expected
    `event_type` and `name`."""
    statement = mock_instance(EdxDoneToggled)
    assert statement.event_type == "edx.done.toggled"
    assert statement.name == "edx.done.toggled"


def test_models_edx_ui_edx_done_toggled_with_valid_statement():
    """Test that a `edx.done.toggled` browser statement has the expected
    `event_type` and `name`."""
    statement = mock_instance(UIEdxDoneToggled)
    assert statement.event_type == "edx.done.toggled"
    assert statement.name == "edx.done.toggled"
