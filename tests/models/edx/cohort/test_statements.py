"""Tests for the peer_instruction event models."""

import json

import pytest
from hypothesis import strategies as st

from ralph.models.edx.cohort.statements import (
    EdxCohortCreated,
    EdxCohortUserAdded,
    EdxCohortUserRemoved,
)
from ralph.models.selector import ModelSelector

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


@pytest.mark.parametrize(
    "class_",
    [EdxCohortCreated, EdxCohortUserAdded, EdxCohortUserRemoved],
)
@custom_given(st.data())
def test_models_edx_cohort_selectors_with_valid_statements(class_, data):
    """Test given a valid cohort edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(data.draw(custom_builds(class_)).json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


@custom_given(EdxCohortCreated)
def test_models_edx_edx_cohort_created_with_valid_statement(
    statement,
):
    """Test that a `edx.cohort.created` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.cohort.created"
    assert statement.name == "edx.cohort.created"


@custom_given(EdxCohortUserAdded)
def test_models_edx_edx_cohort_user_added_with_valid_statement(
    statement,
):
    """Test that a `edx.cohort.user_added` statement has the expected
    `event_type`.
    """
    assert statement.event_type == "edx.cohort.user_added"
    assert statement.name == "edx.cohort.user_added"


@custom_given(EdxCohortUserRemoved)
def test_models_edx_edx_cohort_user_removed_with_valid_statement(
    statement,
):
    """Test that a `edx.cohort.user_removed` statement has the expected
    `event_type`.
    """
    assert statement.event_type == "edx.cohort.user_removed"
    assert statement.name == "edx.cohort.user_removed"
