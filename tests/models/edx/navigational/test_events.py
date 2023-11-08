"""Tests for the navigational models event fields"""

import json
import re

import pytest
from pydantic.error_wrappers import ValidationError

from ralph.models.edx.navigational.fields.events import NavigationalEventField

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(NavigationalEventField)
def test_fields_edx_navigational_events_event_field_with_valid_content(field):
    """Test that a valid `NavigationalEventField` does not raise a
    `ValidationError`.
    """

    assert re.match(
        (
            r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"
            r"type@sequential\+block@[a-f0-9]{32}$"
        ),
        field.id,
    )


@pytest.mark.parametrize(
    "id",
    [
        (
            "block-v2:orgX=CS111+20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS11120_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+tipe@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        "block-v1:orgX=CS111=20_T1+",
        "type@sequentialblock@d0d4a647742943e3951b45d9db8a0ea1",
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943z3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea13"
        ),
    ],
)
@custom_given(NavigationalEventField)
def test_fields_edx_navigational_events_event_field_with_invalid_content(id, field):
    """Test that an invalid `NavigationalEventField` raises a `ValidationError`."""

    invalid_field = json.loads(field.json())
    invalid_field["id"] = id

    with pytest.raises(ValidationError, match="id\n  string does not match regex"):
        NavigationalEventField(**invalid_field)
