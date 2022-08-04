"""Tests for the video event models"""

import json

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

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(UIPlayVideo)
def test_models_edx_ui_play_video_with_valid_statement(
    statement,
):
    """Tests that a `play_video` statement has the expected `event_type`."""

    assert statement.event_type == "play_video"


@custom_given(UIPlayVideo)
def test_models_edx_ui_play_video_selector_with_valid_statement(
    statement,
):
    """Tests given a `play_video` statement the `get_model`
    selector method should return `UIPlayVideo` model.
    """

    statement = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.edx").get_model(statement) is UIPlayVideo


@custom_given(UIPauseVideo)
def test_models_edx_ui_pause_video_with_valid_statement(
    statement,
):
    """Tests that a `pause_video` statement has the expected `event_type`."""

    assert statement.event_type == "pause_video"


@custom_given(UIPauseVideo)
def test_models_edx_ui_pause_video_selector_with_valid_statement(
    statement,
):
    """Tests given a `pause_video` statement the `get_model`
    selector method should return `UIPauseVideo` model.
    """

    statement = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.edx").get_model(statement) is UIPauseVideo


@custom_given(UILoadVideo)
def test_models_edx_ui_load_video_with_valid_statement(
    statement,
):
    """Tests that a `load_video` statement has the expected `event_type` and `name`."""

    assert statement.event_type == "load_video"
    assert statement.name in {"load_video", "edx.video.loaded"}


@custom_given(UILoadVideo)
def test_models_edx_ui_load_video_selector_with_valid_statement(
    statement,
):
    """Tests given a `load_video` statement the `get_model`
    selector method should return `UILoadVideo` model.
    """

    statement = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.edx").get_model(statement) is UILoadVideo


@custom_given(UISeekVideo)
def test_models_edx_ui_seek_video_with_valid_statement(
    statement,
):
    """Tests that a `seek_video` statement has the expected `event_type`."""

    assert statement.event_type == "seek_video"


@custom_given(UISeekVideo)
def test_models_edx_ui_seek_video_selector_with_valid_statement(
    statement,
):
    """Tests given a `seek_video` statement the `get_model`
    selector method should return `UISeekVideo` model.
    """

    statement = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.edx").get_model(statement) is UISeekVideo


@custom_given(UIStopVideo)
def test_models_edx_ui_stop_video_with_valid_statement(
    statement,
):
    """Tests that a `stop_video` statement has the expected `event_type`."""

    assert statement.event_type == "stop_video"


@custom_given(UIStopVideo)
def test_models_edx_ui_stop_video_selector_with_valid_statement(
    statement,
):
    """Tests given a `stop_video` statement the `get_model`
    selector method should return `UIStopVideo` model.
    """

    statement = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.edx").get_model(statement) is UIStopVideo


@custom_given(UIHideTranscript)
def test_models_edx_ui_hide_transcript_with_valid_statement(
    statement,
):
    """Tests that a `hide_transcript` statement has the expected `event_type`
    and `name`.
    """

    assert statement.event_type == "hide_transcript"
    assert statement.name in {"hide_transcript", "edx.video.transcript.hidden"}


@custom_given(UIHideTranscript)
def test_models_edx_ui_hide_transcript_selector_with_valid_statement(
    statement,
):
    """Tests given a `hide_transcript` statement the `get_model`
    selector method should return `UIHideTranscript` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is UIHideTranscript
    )


@custom_given(UIShowTranscript)
def test_models_edx_ui_show_transcript_with_valid_statement(
    statement,
):
    """Tests that a `show_transcript` statement has the expected `event_type`
    and `name.
    """

    assert statement.event_type == "show_transcript"
    assert statement.name in {"show_transcript", "edx.video.transcript.shown"}


@custom_given(UIShowTranscript)
def test_models_edx_ui_show_transcript_selector_with_valid_statement(
    statement,
):
    """Tests given a `show_transcript` statement the `get_model`
    selector method should return `UISHowTranscript` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is UIShowTranscript
    )


@custom_given(UISpeedChangeVideo)
def test_models_edx_ui_speed_change_video_with_valid_statement(
    statement,
):
    """Tests that a `speed_change_video` statement has the expected `event_type`."""

    assert statement.event_type == "speed_change_video"


@custom_given(UISpeedChangeVideo)
def test_models_edx_ui_speed_change_video_selector_with_valid_statement(
    statement,
):
    """Tests given a `speed_change_video` statement the `get_model`
    selector method should return a `UISpeedChangeVideo` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is UISpeedChangeVideo
    )


@custom_given(UIVideoHideCCMenu)
def test_models_edx_ui_vide_hide_cc_menu_with_valid_statement(
    statement,
):
    """Tests that a `video_hide_cc_menu` statement has the expected `event_type`."""

    assert statement.event_type == "video_hide_cc_menu"


@custom_given(UIVideoHideCCMenu)
def test_models_edx_ui_video_hide_cc_menu_selector_with_valid_statement(
    statement,
):
    """Tests given a `video_hide_cc_menu` statement the `get_model`
    selector method should return a `UIVideoHideCCMenu` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is UIVideoHideCCMenu
    )


@custom_given(UIVideoShowCCMenu)
def test_models_edx_ui_video_show_cc_menu_with_valid_statement(
    statement,
):
    """Tests that a `video_show_cc_menu` statement has the expected `event_type`."""

    assert statement.event_type == "video_show_cc_menu"


@custom_given(UIVideoShowCCMenu)
def test_models_edx_ui_video_show_cc_menu_selector_with_valid_statement(
    statement,
):
    """Tests given a `video_show_cc_menu` statement the `get_model`
    selector method should return a `UIVideoShowCCMenu` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is UIVideoShowCCMenu
    )
