"""Tests for the xAPI actor fields"""

import pytest
from pydantic import ValidationError

from ralph.models.xapi.fields.actor import ActorField


def test_models_xapi_fields_actor_actor_field_with_valid_content():
    """Tests that a valid actor field does not raise ValidationErrors."""

    try:
        ActorField(account={"name": "username", "homePage": "https://fun-mooc.fr/"})
    except ValidationError as err:
        pytest.fail("Valid actor field should not raise ValidationErrors: %s" % err)
