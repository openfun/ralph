"""Tests for the peer_instruction event models."""

import json

import pytest
from hypothesis import strategies as st

from ralph.models.edx.teams_related.statements import (
    EdxTeamActivityUpdated,
    EdxTeamChanged,
    EdxTeamCreated,
    EdxTeamDeleted,
    EdxTeamLearnerAdded,
    EdxTeamLearnerRemoved,
    EdxTeamPageViewed,
    EdxTeamSearched,
)
from ralph.models.selector import ModelSelector

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


@pytest.mark.parametrize(
    "class_",
    [
        EdxTeamActivityUpdated,
        EdxTeamChanged,
        EdxTeamCreated,
        EdxTeamDeleted,
        EdxTeamLearnerAdded,
        EdxTeamLearnerRemoved,
        EdxTeamPageViewed,
        EdxTeamSearched,
    ],
)
@custom_given(st.data())
def test_models_edx_teams_related_selectors_with_valid_statements(class_, data):
    """Test given a valid teams_related edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(data.draw(custom_builds(class_)).json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


@custom_given(EdxTeamActivityUpdated)
def test_models_edx_edx_team_activity_updated_with_valid_statement(
    statement,
):
    """Test that a `edx.team.activity_updated` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.team.activity_updated"
    assert statement.name == "edx.team.activity_updated"


@custom_given(EdxTeamChanged)
def test_models_edx_edx_team_changed_with_valid_statement(
    statement,
):
    """Test that a `edx.team.changed` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.team.changed"
    assert statement.name == "edx.team.changed"


@custom_given(EdxTeamCreated)
def test_models_edx_edx_team_created_with_valid_statement(
    statement,
):
    """Test that a `edx.team.created` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.team.created"
    assert statement.name == "edx.team.created"


@custom_given(EdxTeamDeleted)
def test_models_edx_edx_team_deleted_with_valid_statement(
    statement,
):
    """Test that a `edx.team.deleted` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.team.deleted"
    assert statement.name == "edx.team.deleted"


@custom_given(EdxTeamLearnerAdded)
def test_models_edx_edx_team_learner_added_with_valid_statement(
    statement,
):
    """Test that a `edx.team.learner_added` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.team.learner_added"
    assert statement.name == "edx.team.learner_added"


@custom_given(EdxTeamLearnerRemoved)
def test_models_edx_edx_team_learner_removed_with_valid_statement(
    statement,
):
    """Test that a `edx.team.learner_removed` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.team.learner_removed"
    assert statement.name == "edx.team.learner_removed"


@custom_given(EdxTeamPageViewed)
def test_models_edx_edx_team_page_viewed_with_valid_statement(
    statement,
):
    """Test that a `edx.team.page_viewed` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.team.page_viewed"
    assert statement.name == "edx.team.page_viewed"


@custom_given(EdxTeamSearched)
def test_models_edx_edx_team_searched_with_valid_statement(
    statement,
):
    """Test that a `edx.team.searched` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.team.searched"
    assert statement.name == "edx.team.searched"
