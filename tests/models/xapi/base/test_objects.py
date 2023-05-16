"""Tests for the base xAPI `Object` definitions."""

from ralph.models.xapi.base.objects import BaseXapiSubStatement

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(BaseXapiSubStatement)
def test_models_xapi_object_base_sub_statement_type_with_valid_field(field):
    """Tests a valid BaseXapiSubStatement has the expected `objectType` value."""

    assert field.objectType == "SubStatement"
