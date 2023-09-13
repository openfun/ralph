"""Tests for the base xAPI `Group` definitions."""

from ralph.models.xapi.base.groups import BaseXapiGroupCommonProperties

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(BaseXapiGroupCommonProperties)
def test_models_xapi_base_groups_group_common_properties_with_valid_field(
    field,
):
    """Test a valid BaseXapiGroupCommonProperties has the expected
    `objectType` value.
    """

    assert field.objectType == "Group"
