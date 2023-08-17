"""Tests for Ralph ws stream backend."""

import json
from io import BytesIO

import websockets

from ralph.backends.stream.ws import WSStreamBackend, WSStreamBackendSettings

from tests.fixtures.backends import WS_TEST_HOST, WS_TEST_PORT


def test_backends_stream_ws_stream_default_instantiation(monkeypatch, fs):
    """Test the `WSStreamBackend` instantiation."""
    # pylint: disable=invalid-name,unused-argument
    fs.create_file(".env")
    backend_settings_names = ["URI"]
    for name in backend_settings_names:
        monkeypatch.delenv(f"RALPH_BACKENDS__STREAM__WS__{name}", raising=False)

    assert WSStreamBackend.name == "ws"
    assert WSStreamBackend.settings_class == WSStreamBackendSettings
    backend = WSStreamBackend()
    assert not backend.settings.URI

    uri = f"ws://{WS_TEST_HOST}:{WS_TEST_PORT}"
    backend = WSStreamBackend(WSStreamBackendSettings(URI=uri))
    assert backend.settings.URI == uri


def test_backends_stream_ws_stream_stream(ws, monkeypatch, events):
    """Test the `WSStreamBackend` stream method."""
    # pylint: disable=invalid-name,unused-argument
    settings = WSStreamBackendSettings(URI=f"ws://{WS_TEST_HOST}:{WS_TEST_PORT}")

    backend = WSStreamBackend(settings)

    # Mock stdout stream
    class MockStdout:
        """A simple mock for sys.stdout.buffer."""

        buffer = BytesIO()

    mock_stdout = MockStdout()

    try:
        backend.stream(mock_stdout.buffer)
    except websockets.exceptions.ConnectionClosedOK:
        pass

    mock_stdout.buffer.seek(0)
    streamed_events = [json.loads(line) for line in mock_stdout.buffer.readlines()]
    assert streamed_events == events


def test_backends_stream_ws_stream_stream_when_server_stops(ws, monkeypatch, events):
    """Test the WSStreamBackend stream method when the websocket server stops."""
    # pylint: disable=invalid-name,unused-argument
    settings = WSStreamBackendSettings(URI=f"ws://{WS_TEST_HOST}:{WS_TEST_PORT}")
    backend = WSStreamBackend(settings)

    # Mock stdout stream
    class MockStdout:
        """A simple mock for sys.stdout.buffer."""

        buffer = BytesIO()

    mock_stdout = MockStdout()

    try:
        backend.stream(mock_stdout.buffer)
    except websockets.exceptions.ConnectionClosedOK:
        pass

    mock_stdout.buffer.seek(0)
    streamed_events = [json.loads(line) for line in mock_stdout.buffer.readlines()]
    assert streamed_events == events
