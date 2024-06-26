"""Tests for teams-related models event fields."""

import json

import pytest
from pydantic.error_wrappers import ValidationError

from ralph.models.edx.teams_related.fields.events import (
    EdxTeamChangedEventField,
    EdxTeamLearnerAddedEventField,
    EdxTeamLearnerRemovedEventField,
    EdxTeamPageViewedEventField,
)

from tests.factories import mock_instance


def test_models_edx_edx_team_changed_event_field_with_valid_field():
    """Test that a valid `EdxTeamChangedEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(EdxTeamChangedEventField)
    assert len(field.new) <= 1250
    assert len(field.old) <= 1250
    assert len(field.truncated) in (1, 2)


def test_models_edx_edx_team_changed_event_field_with_invalid_new():
    """Test that a valid `EdxTeamChangedEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(EdxTeamChangedEventField)
    invalid_field = json.loads(field.json())
    invalid_field["new"] = "x" * 1251
    with pytest.raises(
        ValidationError,
        match="new\n  String should have at most 1250 characters",
    ):
        EdxTeamChangedEventField(**invalid_field)


def test_models_edx_edx_team_changed_event_field_with_invalid_old():
    """Test that a valid `EdxTeamChangedEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(EdxTeamChangedEventField)
    invalid_field = json.loads(field.json())
    invalid_field["old"] = "x" * 1251
    with pytest.raises(
        ValidationError,
        match="old\n  String should have at most 1250 characters",
    ):
        EdxTeamChangedEventField(**invalid_field)


def test_models_edx_edx_team_learner_added_event_field_with_valid_field():
    """Test that a valid `EdxTeamLearnerAddedEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(EdxTeamLearnerAddedEventField)
    assert field.add_method in (
        "added_on_create",
        "joined_from_team_view",
        "added_by_another_user",
    )


@pytest.mark.parametrize(
    "add_method", ["added on create", "joined from team view", "added by another user"]
)
def test_models_edx_edx_team_learner_added_event_field_with_invalid_add_method(
    add_method,
):
    """Test that a valid `EdxTeamLearnerAddedEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(EdxTeamLearnerAddedEventField)
    invalid_field = json.loads(field.json())
    invalid_field["add_method"] = add_method
    with pytest.raises(ValidationError, match="add_method"):
        EdxTeamLearnerAddedEventField(**invalid_field)


def test_models_edx_edx_team_learner_removed_event_field_with_valid_field():
    """Test that a valid `EdxTeamLearnerRemovedEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(EdxTeamLearnerRemovedEventField)
    assert field.remove_method in ("self_removal", "team_deleted", "removed_by_admin")


@pytest.mark.parametrize(
    "remove_method", ["self removal", "team deleted", "removed by admin"]
)
def test_models_edx_edx_team_learner_removed_event_field_with_invalid_remove_method(
    remove_method,
):
    """Test that a valid `EdxTeamLearnerRemovedEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(EdxTeamLearnerRemovedEventField)
    invalid_field = json.loads(field.json())
    invalid_field["remove_method"] = remove_method
    with pytest.raises(ValidationError, match="remove_method"):
        EdxTeamLearnerRemovedEventField(**invalid_field)


def test_models_edx_edx_team_page_viewed_event_field_with_valid_field():
    """Test that a valid `EdxTeamPageViewedEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(EdxTeamPageViewedEventField)
    assert field.page_name in (
        "browse",
        "edit-team",
        "my-teams",
        "new-team",
        "search-teams",
        "single-team",
        "single-topic",
    )


@pytest.mark.parametrize(
    "page_name",
    [
        "brose",
        "edit team",
        "my teams",
        "new team",
        "search teams",
        "single team",
        "single topic",
    ],
)
def test_models_edx_edx_team_page_viewed_event_field_with_invalid_page_name(page_name):
    """Test that a valid `EdxTeamPageViewedEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(EdxTeamPageViewedEventField)
    invalid_field = json.loads(field.json())
    invalid_field["page_name"] = page_name
    with pytest.raises(ValidationError, match="page_name"):
        EdxTeamPageViewedEventField(**invalid_field)
