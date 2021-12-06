"""Tests for the xAPI actor fields"""

from hypothesis import given, provisional, settings
from hypothesis import strategies as st

from ralph.models.xapi.fields.actors import ActorAccountField, ActorField


@settings(max_examples=1)
@given(
    st.builds(
        ActorField,
        account=st.builds(
            ActorAccountField, name=st.just("username"), homePage=provisional.urls()
        ),
    )
)
def test_models_xapi_fields_actor_account_field_with_valid_content(actor):
    """Tests that an actor field contains an account field."""

    assert hasattr(actor.account, "name")
    assert hasattr(actor.account, "homePage")
