"""Tests for the base xAPI `Group` definitions."""

from ralph.models.xapi.base.groups import BaseXapiGroupCommonProperties

# from tests.fixtures.hypothesis_strategies import custom_given
from tests.factories import mock_xapi_instance


def test_models_xapi_base_groups_group_common_properties_with_valid_field():
    """Test a valid BaseXapiGroupCommonProperties has the expected
    `objectType` value.
    """
    field = mock_xapi_instance(BaseXapiGroupCommonProperties)

    assert field.objectType == "Group"
