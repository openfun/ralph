"""Tests for the base xAPI `Object` definitions."""

from ralph.models.xapi.base.objects import BaseXapiSubStatement

from tests.factories import mock_xapi_instance


def test_models_xapi_object_base_sub_statement_type_with_valid_field():
    """Test a valid BaseXapiSubStatement has the expected `objectType` value."""
    field = mock_xapi_instance(BaseXapiSubStatement)

    assert field.objectType == "SubStatement"
