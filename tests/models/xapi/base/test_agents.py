"""Tests for the base xAPI `Agent` definitions."""

import json
import re

import pytest
from pydantic import ValidationError

from ralph.models.xapi.base.agents import BaseXapiAgentWithMboxSha1Sum

# from tests.fixtures.hypothesis_strategies import custom_given

from tests.factories import mock_instance


def test_models_xapi_base_agent_with_mbox_sha1_sum_ifi_with_valid_field():
    """Test a valid BaseXapiAgentWithMboxSha1Sum has the expected
    `mbox_sha1sum` regex.
    """
    field = mock_instance(BaseXapiAgentWithMboxSha1Sum)

    assert re.match(r"^[0-9a-f]{40}$", field.mbox_sha1sum)


@pytest.mark.parametrize(
    "mbox_sha1sum",
    [
        "1baccll9xkidkd4re9n24djgfh939g7dhyjm3li3",
        "1baccde9",
        "1baccdd9abcdfd4ae9b24dedfa939c7deffa3db3a7",
    ],
)
def test_models_xapi_base_agent_with_mbox_sha1_sum_ifi_with_invalid_field(
    mbox_sha1sum
):
    """Test an invalid `mbox_sha1sum` property in
    BaseXapiAgentWithMboxSha1Sum raises a `ValidationError`.
    """
    
    field = mock_instance(BaseXapiAgentWithMboxSha1Sum)

    invalid_field = json.loads(field.json())
    invalid_field["mbox_sha1sum"] = mbox_sha1sum

    with pytest.raises(
        ValidationError, match="mbox_sha1sum\n  string does not match regex"
    ):
        BaseXapiAgentWithMboxSha1Sum(**invalid_field)
