"""Tests for the xAPI navigation statements."""

import json

import pytest
from hypothesis import strategies as st

from ralph.models.selector import ModelSelector
from ralph.models.xapi.navigation.statements import PageTerminated, PageViewed

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


@pytest.mark.parametrize("class_", [PageTerminated, PageViewed])
@custom_given(st.data())
def test_models_xapi_navigational_selectors_with_valid_statements(class_, data):
    """Tests given a valid navigational xAPI statement the `get_first_model`
    selector method should return the expected model.
    """

    statement = json.loads(data.draw(custom_builds(class_)).json())
    model = ModelSelector(module="ralph.models.xapi").get_first_model(statement)
    assert model is class_


@custom_given(PageTerminated)
def test_models_xapi_page_terminated_statement(statement):
    """Tests that a page_terminated statement has the expected verb.id and
    object.definition.
    """

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/terminated"
    assert statement.object.definition.type == "http://activitystrea.ms/schema/1.0/page"


@custom_given(PageViewed)
def test_models_xapi_page_viewed_statement(statement):
    """Tests that a page_viewed statement has the expected verb.id and
    object.definition.
    """

    assert statement.verb.id == "http://id.tincanapi.com/verb/viewed"
    assert statement.object.definition.type == "http://activitystrea.ms/schema/1.0/page"
