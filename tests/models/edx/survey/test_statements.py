"""Tests for the survey event models."""

import json

import pytest
from hypothesis import strategies as st

from ralph.models.edx.survey.statements import (
    XBlockSurveySubmitted,
    XBlockSurveyViewResults,
)
from ralph.models.selector import ModelSelector

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


@pytest.mark.parametrize(
    "class_",
    [XBlockSurveySubmitted, XBlockSurveyViewResults],
)
@custom_given(st.data())
def test_models_edx_survey_selectors_with_valid_statements(class_, data):
    """Test given a valid survey edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(data.draw(custom_builds(class_)).json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


@custom_given(XBlockSurveySubmitted)
def test_models_edx_xblock_survey_submitted_with_valid_statement(
    statement,
):
    """Test that a `xblock.survey.submitted` statement has the expected
    `event_type` and `name`."""
    assert statement.event_type == "xblock.survey.submitted"
    assert statement.name == "xblock.survey.submitted"


@custom_given(XBlockSurveyViewResults)
def test_models_edx_xblock_survey_view_results_with_valid_statement(
    statement,
):
    """Test that a `xblock.survey.view_results` statement has the expected
    `event_type` and `name`."""
    assert statement.event_type == "xblock.survey.view_results"
    assert statement.name == "xblock.survey.view_results"
