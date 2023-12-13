"""Tests for the xAPI navigation statements."""

import json

import pytest
from hypothesis import settings
from hypothesis import strategies as st

from ralph.models.selector import ModelSelector
from ralph.models.xapi.navigation.statements import PageTerminated, PageViewed

# from tests.fixtures.hypothesis_strategies import custom_builds, custom_given
from tests.factories import mock_xapi_instance

@pytest.mark.parametrize("class_", [PageTerminated, PageViewed])
def test_models_xapi_navigation_selectors_with_valid_statements(class_):
    """Test given a valid navigation xAPI statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(mock_xapi_instance(class_).json())
    model = ModelSelector(module="ralph.models.xapi").get_first_model(statement)
    assert model is class_


def test_models_xapi_navigation_page_terminated_with_valid_statement():
    """Test that a valid page_terminated statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """
    statement = mock_xapi_instance(PageTerminated)
    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/terminated"
    assert statement.object.definition.type == "http://activitystrea.ms/schema/1.0/page"


def test_models_xapi_page_viewed_with_valid_statement():
    """Test that a valid page_viewed statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """
    statement = mock_xapi_instance(PageViewed)
    assert statement.verb.id == "http://id.tincanapi.com/verb/viewed"
    assert statement.object.definition.type == "http://activitystrea.ms/schema/1.0/page"
