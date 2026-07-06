"""Tests for the base xAPI `Group` definitions."""

import pytest
from pydantic import ValidationError

from ralph.models.xapi.base.groups import (
    BaseXapiGroupCommonProperties,
    BaseXapiIdentifiedGroupWithMbox,
    BaseXapiIdentifiedGroupWithMboxSha1Sum,
)

from tests.factories import mock_xapi_instance


def test_models_xapi_base_groups_group_common_properties_with_valid_field():
    """Test a valid BaseXapiGroupCommonProperties has the expected
    `objectType` value.
    """
    field = mock_xapi_instance(BaseXapiGroupCommonProperties)

    assert field.objectType == "Group"


@pytest.mark.parametrize(
    "group",
    [
        {
            "name": "d75662f7c72c8d12267712aaf31b649cdab13cb8",
            "mbox_sha1sum": "6395037c217b04eae94355900bcaf014772c7d7c",
            "objectType": "Group",
        },
        {
            "name": "d75662f7c72c8d12267712aaf31b649cdab13cb8",
            "mbox_sha1sum": "6395037c217b04eae94355900bcaf014772c7d7c",
            "objectType": "Group",
            "member": [],
        },
    ],
)
def test_models_xapi_base_group_mbox_sha1sum_valid(group):
    """Test an invalid group with `mbox_sha1sum` property"""

    try:
        BaseXapiIdentifiedGroupWithMboxSha1Sum(**group)
    except ValidationError as err:
        pytest.fail(f"Valid statement should not raise exceptions: {err}")


@pytest.mark.parametrize(
    "group",
    [
        {
            "name": "d75662f7c72c8d12267712aaf31b649cdab13cb8",
            "mbox": "mailto:foob@r.com",
            "objectType": "Group",
        },
        {
            "name": "d75662f7c72c8d12267712aaf31b649cdab13cb8",
            "mbox": "mailto:foob@r.com",
            "objectType": "Group",
            "member": [],
        },
    ],
)
def test_models_xapi_base_group_mbox_valid(group):
    """Test an invalid group with `mbox` property"""

    try:
        BaseXapiIdentifiedGroupWithMbox(**group)
    except ValidationError as err:
        pytest.fail(f"Valid statement should not raise exceptions: {err}")
