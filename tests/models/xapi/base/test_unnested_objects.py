"""Tests for the base xAPI `Object` definitions."""

import json
import re

import pytest
from pydantic import ValidationError

from ralph.models.xapi.base.unnested_objects import (
    BaseXapiActivityInteractionDefinition,
    BaseXapiInteractionComponent,
    BaseXapiStatementRef,
)

from tests.factories import mock_xapi_instance


def test_models_xapi_base_object_statement_ref_type_with_valid_field():
    """Test a valid BaseXapiStatementRef has the expected `objectType` value."""
    field = mock_xapi_instance(BaseXapiStatementRef)
    assert field.objectType == "StatementRef"


def test_models_xapi_base_object_interaction_component_with_valid_field():
    """Test a valid BaseXapiInteractionComponent has the expected `id` regex."""
    field = mock_xapi_instance(BaseXapiInteractionComponent)
    assert re.match(r"^[^\s]+$", field.id)


@pytest.mark.parametrize(
    "id_value",
    [" test_id", "\ntest"],
)
def test_models_xapi_base_object_interaction_component_with_invalid_field(id_value):
    """Test an invalid `id` property in
    BaseXapiInteractionComponent raises a `ValidationError`.
    """
    field = mock_xapi_instance(BaseXapiInteractionComponent)

    invalid_property = json.loads(field.json())
    invalid_property["id"] = id_value

    with pytest.raises(ValidationError, match="id\n  String should match pattern"):
        BaseXapiInteractionComponent(**invalid_property)


def test_models_xapi_base_object_activity_type_interaction_definition_with_valid_field():  # noqa: E501
    """Test a valid BaseXapiActivityInteractionDefinition has the expected
    `objectType` value.
    """
    field = mock_xapi_instance(BaseXapiActivityInteractionDefinition)

    assert field.interactionType in (
        "true-false",
        "choice",
        "fill-in",
        "long-fill-in",
        "matching",
        "performance",
        "sequencing",
        "likert",
        "numeric",
        "other",
    )
