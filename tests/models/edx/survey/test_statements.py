"""Tests for the survey event models."""

import json

import pytest

from ralph.models.edx.survey.statements import (
    XBlockSurveySubmitted,
    XBlockSurveyViewResults,
)
from ralph.models.selector import ModelSelector

from tests.factories import mock_instance


@pytest.mark.parametrize(
    "class_",
    [XBlockSurveySubmitted, XBlockSurveyViewResults],
)
def test_models_edx_survey_selectors_with_valid_statements(class_):
    """Test given a valid survey edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(mock_instance(class_).model_dump_json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


def test_models_edx_xblock_survey_submitted_with_valid_statement():
    """Test that a `xblock.survey.submitted` statement has the expected
    `event_type` and `name`."""
    statement = mock_instance(XBlockSurveySubmitted)
    assert statement.event_type == "xblock.survey.submitted"
    assert statement.name == "xblock.survey.submitted"


def test_models_edx_xblock_survey_view_results_with_valid_statement():
    """Test that a `xblock.survey.view_results` statement has the expected
    `event_type` and `name`."""
    statement = mock_instance(XBlockSurveyViewResults)
    assert statement.event_type == "xblock.survey.view_results"
    assert statement.name == "xblock.survey.view_results"
