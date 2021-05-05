"""Tests for the xAPI page_viewed statement"""

from hypothesis import given, provisional, settings
from hypothesis import strategies as st

from ralph.models.xapi.fields.actors import ActorAccountField, ActorField
from ralph.models.xapi.fields.objects import PageObjectField
from ralph.models.xapi.page_viewed import PageViewed


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
    """Tests that a page_viewed statement has the expected verb.id and object.definition."""

    assert statement.verb.id == "http://id.tincanapi.com/verb/viewed"
    assert statement.object.definition.type == "http://activitystrea.ms/schema/1.0/page"
