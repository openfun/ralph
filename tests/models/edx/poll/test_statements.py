"""Tests for the poll event models."""

import json

import pytest

from ralph.models.edx.poll.statements import XBlockPollSubmitted, XBlockPollViewResults
from ralph.models.selector import ModelSelector

from tests.factories import mock_instance


@pytest.mark.parametrize(
    "class_",
    [XBlockPollSubmitted, XBlockPollViewResults],
)
def test_models_edx_poll_selectors_with_valid_statements(class_):
    """Test given a valid poll edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(mock_instance(class_).model_dump_json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


def test_models_edx_xblock_poll_submitted_with_valid_statement():
    """Test that a `xblock.poll.submitted` statement has the expected
    `event_type` and `name`."""
    statement = mock_instance(XBlockPollSubmitted)
    assert statement.event_type == "xblock.poll.submitted"
    assert statement.name == "xblock.poll.submitted"


def test_models_edx_xblock_poll_view_results_with_valid_statement():
    """Test that a `xblock.poll.view_results` statement has the expected
    `event_type` and `name`."""
    statement = mock_instance(XBlockPollViewResults)
    assert statement.event_type == "xblock.poll.view_results"
    assert statement.name == "xblock.poll.view_results"
