"""Tests for the peer_instruction event models."""

import json

import pytest

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

from tests.factories import mock_instance


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
def test_models_edx_teams_related_selectors_with_valid_statements(class_):
    """Test given a valid teams_related edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(mock_instance(class_).model_dump_json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


def test_models_edx_edx_team_activity_updated_with_valid_statement():
    """Test that a `edx.team.activity_updated` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxTeamActivityUpdated)
    assert statement.event_type == "edx.team.activity_updated"
    assert statement.name == "edx.team.activity_updated"


def test_models_edx_edx_team_changed_with_valid_statement():
    """Test that a `edx.team.changed` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxTeamChanged)
    assert statement.event_type == "edx.team.changed"
    assert statement.name == "edx.team.changed"


def test_models_edx_edx_team_created_with_valid_statement():
    """Test that a `edx.team.created` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxTeamCreated)
    assert statement.event_type == "edx.team.created"
    assert statement.name == "edx.team.created"


def test_models_edx_edx_team_deleted_with_valid_statement():
    """Test that a `edx.team.deleted` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxTeamDeleted)
    assert statement.event_type == "edx.team.deleted"
    assert statement.name == "edx.team.deleted"


def test_models_edx_edx_team_learner_added_with_valid_statement():
    """Test that a `edx.team.learner_added` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxTeamLearnerAdded)
    assert statement.event_type == "edx.team.learner_added"
    assert statement.name == "edx.team.learner_added"


def test_models_edx_edx_team_learner_removed_with_valid_statement():
    """Test that a `edx.team.learner_removed` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxTeamLearnerRemoved)
    assert statement.event_type == "edx.team.learner_removed"
    assert statement.name == "edx.team.learner_removed"


def test_models_edx_edx_team_page_viewed_with_valid_statement():
    """Test that a `edx.team.page_viewed` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxTeamPageViewed)
    assert statement.event_type == "edx.team.page_viewed"
    assert statement.name == "edx.team.page_viewed"


def test_models_edx_edx_team_searched_with_valid_statement():
    """Test that a `edx.team.searched` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxTeamSearched)
    assert statement.event_type == "edx.team.searched"
    assert statement.name == "edx.team.searched"
