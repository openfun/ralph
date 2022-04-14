"""Tests for Ralph ws stream backend"""

import json
from io import BytesIO

import pytest
import websockets

from ralph.backends.stream.ws import WSStream

from tests.fixtures.backends import WS_TEST_HOST, WS_TEST_PORT


def test_backends_stream_ws_stream_instantiation(ws):
    """Tests the WSStream backend instantiation."""
    # pylint: disable=invalid-name,unused-argument

    assert WSStream.name == "ws"

    error = "missing 1 required positional argument: 'uri'"
    with pytest.raises(TypeError, match=error):
        WSStream()  # pylint: disable=no-value-for-parameter

    uri = f"ws://{WS_TEST_HOST}:{WS_TEST_PORT}"
    client = WSStream(uri)
    assert client.uri == uri


def test_backends_stream_ws_stream_stream(ws, monkeypatch, events):
    """Tests the WSStream backend stream method."""
    # pylint: disable=invalid-name,unused-argument

    client = WSStream(f"ws://{WS_TEST_HOST}:{WS_TEST_PORT}")

    # Mock stdout stream
    class MockStdout:
        """A simple mock for sys.stdout.buffer."""

        buffer = BytesIO()

    mock_stdout = MockStdout()

    try:
        client.stream(mock_stdout.buffer)
    except websockets.exceptions.ConnectionClosedOK:
        pass

    mock_stdout.buffer.seek(0)
    streamed_events = [json.loads(line) for line in mock_stdout.buffer.readlines()]
    assert streamed_events == events


def test_backends_stream_ws_stream_stream_when_server_stops(ws, monkeypatch, events):
    """Tests the WSStream backend stream method when the websocket server stops."""
    # pylint: disable=invalid-name,unused-argument

    client = WSStream(f"ws://{WS_TEST_HOST}:{WS_TEST_PORT}")

    # Mock stdout stream
    class MockStdout:
        """A simple mock for sys.stdout.buffer."""

        buffer = BytesIO()

    mock_stdout = MockStdout()

    try:
        client.stream(mock_stdout.buffer)
    except websockets.exceptions.ConnectionClosedOK:
        pass

    mock_stdout.buffer.seek(0)
    streamed_events = [json.loads(line) for line in mock_stdout.buffer.readlines()]
    assert streamed_events == events
