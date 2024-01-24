"""Tests for the base event model."""

import json
import re

import pytest
from pydantic import ValidationError

from ralph.models.edx.base import BaseEdxModel

from tests.factories import mock_instance


def test_models_edx_base_edx_model_with_valid_statement():
    """Test that a valid base `Edx` statement does not raise a `ValidationError`."""
    statement = mock_instance(BaseEdxModel)

    assert len(statement.username) == 0 or (len(statement.username) in range(2, 31, 1))
    assert (
        re.match(r"^course-v1:.+\+.+\+.+$", statement.context.course_id)
        or statement.context.course_id == ""
    )


@pytest.mark.parametrize(
    "course_id",
    [
        "course-v1:+course+not_empty",
        "course-v1:org",
        "course-v1:org+course",
        "course-v1:org+course+",
    ],
)
def test_models_edx_base_edx_model_with_invalid_statement(course_id):
    """Test that an invalid base `Edx` statement raises a `ValidationError`."""
    statement = mock_instance(BaseEdxModel)
    invalid_statement = json.loads(statement.model_dump_json())
    invalid_statement["context"]["course_id"] = course_id

    error = "String should match pattern"

    with pytest.raises(ValidationError, match=error):
        BaseEdxModel(**invalid_statement)
