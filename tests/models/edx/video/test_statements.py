"""Tests for the video event models."""

import json

import pytest

from ralph.models.edx.video.statements import (
    UIHideTranscript,
    UILoadVideo,
    UIPauseVideo,
    UIPlayVideo,
    UISeekVideo,
    UIShowTranscript,
    UISpeedChangeVideo,
    UIStopVideo,
    UIVideoHideCCMenu,
    UIVideoShowCCMenu,
)
from ralph.models.selector import ModelSelector

from tests.factories import mock_instance


@pytest.mark.parametrize(
    "class_",
    [
        UIHideTranscript,
        UILoadVideo,
        UIPauseVideo,
        UIPlayVideo,
        UISeekVideo,
        UIShowTranscript,
        UISpeedChangeVideo,
        UIStopVideo,
        UIVideoHideCCMenu,
        UIVideoShowCCMenu,
    ],
)
def test_models_edx_video_selectors_with_valid_statements(class_):
    """Test given a valid video edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(mock_instance(class_).model_dump_json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


def test_models_edx_ui_play_video_with_valid_statement():
    statement = mock_instance(UIPlayVideo)
    """Test that a `play_video` statement has the expected `event_type`."""
    assert statement.event_type == "play_video"


def test_models_edx_ui_pause_video_with_valid_statement():
    statement = mock_instance(UIPauseVideo)
    """Test that a `pause_video` statement has the expected `event_type`."""
    assert statement.event_type == "pause_video"


def test_models_edx_ui_load_video_with_valid_statement():
    statement = mock_instance(UILoadVideo)
    """Test that a `load_video` statement has the expected `event_type` and `name`."""
    assert statement.event_type == "load_video"
    assert statement.name in {"load_video", "edx.video.loaded"}


def test_models_edx_ui_seek_video_with_valid_statement():
    statement = mock_instance(UISeekVideo)
    """Test that a `seek_video` statement has the expected `event_type`."""
    assert statement.event_type == "seek_video"


def test_models_edx_ui_stop_video_with_valid_statement():
    statement = mock_instance(UIStopVideo)
    """Test that a `stop_video` statement has the expected `event_type`."""
    assert statement.event_type == "stop_video"


def test_models_edx_ui_hide_transcript_with_valid_statement():
    """Test that a `hide_transcript` statement has the expected `event_type`
    and `name`.
    """
    statement = mock_instance(UIHideTranscript)
    assert statement.event_type == "hide_transcript"
    assert statement.name in {"hide_transcript", "edx.video.transcript.hidden"}


def test_models_edx_ui_show_transcript_with_valid_statement():
    """Test that a `show_transcript` statement has the expected `event_type`
    and `name.
    """
    statement = mock_instance(UIShowTranscript)
    assert statement.event_type == "show_transcript"
    assert statement.name in {"show_transcript", "edx.video.transcript.shown"}


def test_models_edx_ui_speed_change_video_with_valid_statement():
    """Test that a `speed_change_video` statement has the expected `event_type`."""
    statement = mock_instance(UISpeedChangeVideo)
    assert statement.event_type == "speed_change_video"


def test_models_edx_ui_vide_hide_cc_menu_with_valid_statement():
    """Test that a `video_hide_cc_menu` statement has the expected `event_type`."""
    statement = mock_instance(UIVideoHideCCMenu)
    assert statement.event_type == "video_hide_cc_menu"


def test_models_edx_ui_video_show_cc_menu_with_valid_statement():
    """Test that a `video_show_cc_menu` statement has the expected `event_type`."""
    statement = mock_instance(UIVideoShowCCMenu)
    assert statement.event_type == "video_show_cc_menu"
