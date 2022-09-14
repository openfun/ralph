"""Tests for the xAPI navigation statements."""

import json

from ralph.models.selector import ModelSelector
from ralph.models.xapi.navigation.statements import PageTerminated, PageViewed

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(PageTerminated)
def test_models_xapi_page_terminated_statement(statement):
    """Tests that a page_terminated statement has the expected verb.id and
    object.definition.
    """

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/terminated"
    assert statement.object.definition.type == "http://activitystrea.ms/schema/1.0/page"


@custom_given(PageTerminated)
def test_models_xapi_page_terminated_selector_with_valid_statement(statement):
    """Tests given a page terminated statement, the get_model method should return
    PageTerminated model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.xapi").get_model(statement) is PageTerminated
    )


@custom_given(PageViewed)
def test_models_xapi_page_viewed_statement(statement):
    """Tests that a page_viewed statement has the expected verb.id and
    object.definition.
    """

    assert statement.verb.id == "http://id.tincanapi.com/verb/viewed"
    assert statement.object.definition.type == "http://activitystrea.ms/schema/1.0/page"


@custom_given(PageViewed)
def test_models_xapi_page_viewed_selector_with_valid_statement(statement):
    """Tests given a page viewed statement, the get_model method should return
    PageViewed model.
    """

    statement = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.xapi").get_model(statement) is PageViewed
