"""Tests for the BaseXapiStatement."""

import pytest
from pydantic import ValidationError

from ralph.api.models import LaxStatement

from tests.factories import mock_xapi_instance


@pytest.mark.parametrize(
    "field",
    ["actor", "verb", "object"],
)
def test_api_models_laxstatement_must_use_actor_verb_and_object(field):
    """Test that the statement raises an exception if required fields are missing.

    XAPI-00003
    An LRS rejects with error code 400 Bad Request a Statement which does not contain an
    "actor" property.
    XAPI-00004
    An LRS rejects with error code 400 Bad Request a Statement which does not contain a
    "verb" property.
    XAPI-00005
    An LRS rejects with error code 400 Bad Request a Statement which does not contain an
    "object" property.
    """

    statement = mock_xapi_instance(LaxStatement)

    statement = statement.model_dump(exclude_none=True)
    del statement[field]
    with pytest.raises(ValidationError, match="Field required"):
        LaxStatement(**statement)


def test_api_models_laxstatement_should_not_change_fields():
    """Test that the statement fields should not be changed by validation."""

    object_id = "https://localhost:443/course/1"
    verb_id = "https://localhost:443/didthat"
    statement = mock_xapi_instance(LaxStatement)

    statement = statement.model_dump(exclude_none=True)
    statement["object"]["id"] = object_id
    statement["verb"]["id"] = verb_id

    try:
        output = LaxStatement(**statement)
    except ValidationError as err:
        pytest.fail(f"Valid statement should not raise exceptions: {err}")

    assert output.object.id == object_id
    assert output.verb.id == verb_id
