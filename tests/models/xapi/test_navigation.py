"""Tests for the xAPI navigation statements"""

import json

from hypothesis import given, provisional, settings
from hypothesis import strategies as st

from ralph.models.selector import ModelSelector
from ralph.models.xapi.fields.actors import ActorAccountField, ActorField
from ralph.models.xapi.navigation.fields.objects import PageObjectField
from ralph.models.xapi.navigation.statements import PageTerminated, PageViewed


@settings(max_examples=1)
@given(
    st.builds(
        PageTerminated,
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(PageObjectField, id=provisional.urls()),
    )
)
def test_models_xapi_page_terminated_statement(statement):
    """Tests that a page_terminated statement has the expected verb.id and
    object.definition.
    """

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/terminated"
    assert statement.object.definition.type == "http://activitystrea.ms/schema/1.0/page"


@settings(max_examples=1)
@given(
    st.builds(
        PageTerminated,
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(PageObjectField, id=provisional.urls()),
    )
)
def test_models_xapi_page_terminated_selector_with_valid_statement(statement):
    """Tests given a page terminated statement, the get_model method should return
    PageTerminated model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.xapi").get_model(statement) is PageTerminated
    )


@settings(max_examples=1)
@given(
    st.builds(
        PageViewed,
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(PageObjectField, id=provisional.urls()),
    )
)
def test_models_xapi_page_viewed_statement(statement):
    """Tests that a page_viewed statement has the expected verb.id and
    object.definition.
    """

    assert statement.verb.id == "http://id.tincanapi.com/verb/viewed"
    assert statement.object.definition.type == "http://activitystrea.ms/schema/1.0/page"


@settings(max_examples=1)
@given(
    st.builds(
        PageViewed,
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(PageObjectField, id=provisional.urls()),
    )
)
def test_models_xapi_page_viewed_selector_with_valid_statement(statement):
    """Tests given a page viewed statement, the get_model method should return
    PageViewed model.
    """

    statement = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.xapi").get_model(statement) is PageViewed
