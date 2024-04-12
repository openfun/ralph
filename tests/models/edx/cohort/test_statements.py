"""Tests for the peer_instruction event models."""

import json

import pytest

from ralph.models.edx.cohort.statements import (
    EdxCohortCreated,
    EdxCohortUserAdded,
    EdxCohortUserRemoved,
)
from ralph.models.selector import ModelSelector

from tests.factories import mock_instance


@pytest.mark.parametrize(
    "class_",
    [EdxCohortCreated, EdxCohortUserAdded, EdxCohortUserRemoved],
)
def test_models_edx_cohort_selectors_with_valid_statements(class_):
    """Test given a valid cohort edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(mock_instance(class_).model_dump_json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


def test_models_edx_edx_cohort_created_with_valid_statement():
    """Test that a `edx.cohort.created` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxCohortCreated)
    assert statement.event_type == "edx.cohort.created"
    assert statement.name == "edx.cohort.created"


def test_models_edx_edx_cohort_user_added_with_valid_statement():
    """Test that a `edx.cohort.user_added` statement has the expected
    `event_type`.
    """
    statement = mock_instance(EdxCohortUserAdded)
    assert statement.event_type == "edx.cohort.user_added"
    assert statement.name == "edx.cohort.user_added"


def test_models_edx_edx_cohort_user_removed_with_valid_statement():
    """Test that a `edx.cohort.user_removed` statement has the expected
    `event_type`.
    """
    statement = mock_instance(EdxCohortUserRemoved)
    assert statement.event_type == "edx.cohort.user_removed"
    assert statement.name == "edx.cohort.user_removed"
