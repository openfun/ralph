"""Tests for the base event model."""

import json
import re

import pytest
from pydantic.error_wrappers import ValidationError

from ralph.models.edx.base import BaseEdxModel

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(BaseEdxModel)
def test_models_edx_base_edx_model_with_valid_statement(statement):
    """Test that a valid base `Edx` statement does not raise a `ValidationError`."""
    assert len(statement.username) == 0 or (len(statement.username) in range(2, 31, 1))
    assert (
        re.match(r"^course-v1:.+\+.+\+.+$", statement.context.course_id)
        or statement.context.course_id == ""
    )


@pytest.mark.parametrize(
    "course_id,error",
    [
        (
            "course-v1:+course+not_empty",
            "course_id\n  string does not match regex",
        ),
        (
            "course-v1:org",
            "course_id\n  string does not match regex",
        ),
        (
            "course-v1:org+course",
            "course_id\n  string does not match regex",
        ),
        (
            "course-v1:org+course+",
            "course_id\n  string does not match regex",
        ),
    ],
)
@custom_given(BaseEdxModel)
def test_models_edx_base_edx_model_with_invalid_statement(course_id, error, statement):
    """Test that an invalid base `Edx` statement raises a `ValidationError`."""
    invalid_statement = json.loads(statement.json())
    invalid_statement["context"]["course_id"] = course_id

    with pytest.raises(ValidationError, match=error):
        BaseEdxModel(**invalid_statement)
