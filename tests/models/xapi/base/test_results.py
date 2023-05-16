"""Tests for the base xAPI `Result` definitions."""

import json

import pytest
from pydantic import ValidationError

from ralph.models.xapi.base.results import BaseXapiResultScore

from tests.fixtures.hypothesis_strategies import custom_given


@pytest.mark.parametrize(
    "raw_value, min_value, max_value, error_msg",
    [
        (2, 5, 10, "min cannot be greater than raw"),
        (2, 10, 5, "min cannot be greater than max"),
        (12, 5, 10, "raw cannot be greater than max"),
    ],
)
@custom_given(BaseXapiResultScore)
def test_models_xapi_base_result_score_with_invalid_raw_min_max_relation(
    raw_value, min_value, max_value, error_msg, field
):
    """Tests invalids `raw`,`min`,`max` relation in BaseXapiResultScore raises
    ValidationError.
    """

    invalid_field = json.loads(field.json())
    invalid_field["raw"] = raw_value
    invalid_field["min"] = min_value
    invalid_field["max"] = max_value

    with pytest.raises(ValidationError, match=error_msg):
        BaseXapiResultScore(**invalid_field)
