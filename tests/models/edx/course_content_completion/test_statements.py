"""Tests for the Course Content Completion event models."""

import json

import pytest
from hypothesis import strategies as st

from ralph.models.edx.course_content_completion.statements import (
    EdxDoneToggled,
    UIEdxDoneToggled,
)
from ralph.models.selector import ModelSelector

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


@pytest.mark.parametrize(
    "class_",
    [EdxDoneToggled, UIEdxDoneToggled],
)
@custom_given(st.data())
def test_models_edx_course_content_completion_selectors_with_valid_statements(
    class_, data
):
    """Test given a valid course content completion edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(data.draw(custom_builds(class_)).json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


@custom_given(EdxDoneToggled)
def test_models_edx_edx_done_toggled_with_valid_statement(
    statement,
):
    """Test that a `edx.done.toggled` server statement has the expected
    `event_type` and `name`."""
    assert statement.event_type == "edx.done.toggled"
    assert statement.name == "edx.done.toggled"


@custom_given(UIEdxDoneToggled)
def test_models_edx_ui_edx_done_toggled_with_valid_statement(
    statement,
):
    """Test that a `edx.done.toggled` browser statement has the expected
    `event_type` and `name`."""
    assert statement.event_type == "edx.done.toggled"
    assert statement.name == "edx.done.toggled"
