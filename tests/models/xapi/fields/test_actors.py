"""Tests for the xAPI actor fields"""

from ralph.models.xapi.fields.actors import ActorField

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(ActorField)
def test_models_xapi_fields_actor_account_field_with_valid_content(actor):
    """Tests that an actor field contains an account field."""

    assert hasattr(actor.account, "name")
    assert hasattr(actor.account, "homePage")
