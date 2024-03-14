"""Tests for the poll event models."""

import json

import pytest
from hypothesis import strategies as st

from ralph.models.edx.poll.statements import XBlockPollSubmitted, XBlockPollViewResults
from ralph.models.selector import ModelSelector

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


@pytest.mark.parametrize(
    "class_",
    [XBlockPollSubmitted, XBlockPollViewResults],
)
@custom_given(st.data())
def test_models_edx_poll_selectors_with_valid_statements(class_, data):
    """Test given a valid poll edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(data.draw(custom_builds(class_)).json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


@custom_given(XBlockPollSubmitted)
def test_models_edx_xblock_poll_submitted_with_valid_statement(
    statement,
):
    """Test that a `xblock.poll.submitted` statement has the expected
    `event_type` and `name`."""
    assert statement.event_type == "xblock.poll.submitted"
    assert statement.name == "xblock.poll.submitted"


@custom_given(XBlockPollViewResults)
def test_models_edx_xblock_poll_view_results_with_valid_statement(
    statement,
):
    """Test that a `xblock.poll.view_results` statement has the expected
    `event_type` and `name`."""
    assert statement.event_type == "xblock.poll.view_results"
    assert statement.name == "xblock.poll.view_results"
