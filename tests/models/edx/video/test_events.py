"""Tests for video models event fields."""

import json

import pytest
from pydantic.error_wrappers import ValidationError

from ralph.models.edx.video.fields.events import SpeedChangeVideoEventField

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(SpeedChangeVideoEventField)
def test_models_edx_speed_change_video_event_field_with_valid_field(field):
    """Tests that a valid `SpeedChangeVideoEventField` does not raise a
    `ValidationError`.
    """

    assert field.old_speed in ["0.75", "1.0", "1.25", "1.50", "2.0"]
    assert field.new_speed in ["0.75", "1.0", "1.25", "1.50", "2.0"]


@pytest.mark.parametrize(
    "old_speed",
    ["0,75", "1", "-1.0", "1.30"],
)
@custom_given(SpeedChangeVideoEventField)
def test_models_edx_speed_change_video_event_field_with_invalid_old_speed_value(
    old_speed, field
):  # noqa
    """Tests that an invalid `old_speed` value in
    `SpeedChangeVideoEventField` raises a `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["old_speed"] = old_speed

    with pytest.raises(ValidationError, match="old_speed\n  unexpected value"):
        SpeedChangeVideoEventField(**invalid_field)


@pytest.mark.parametrize(
    "new_speed",
    ["0,75", "1", "-1.0", "1.30"],
)
@custom_given(SpeedChangeVideoEventField)
def test_models_edx_speed_change_video_event_field_with_invalid_new_speed_value(
    new_speed, field
):  # noqa
    """Tests that an invalid `new_speed` value in
    `SpeedChangeVideoEventField` raises a `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["new_speed"] = new_speed

    with pytest.raises(ValidationError, match="new_speed\n  unexpected value"):
        SpeedChangeVideoEventField(**invalid_field)
