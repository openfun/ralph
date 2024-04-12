"""Tests for Ralph ws stream backend."""

import json
import logging
import re

import pytest
import websockets
from pydantic import AnyUrl, TypeAdapter

from ralph.backends.data.async_ws import AsyncWSDataBackend, WSDataBackendSettings
from ralph.backends.data.base import DataBackendStatus
from ralph.exceptions import BackendException, BackendParameterException

from tests.fixtures.backends import WS_TEST_HOST, WS_TEST_PORT


def test_backends_data_async_ws_default_instantiation(caplog, monkeypatch, fs):
    """Test the `AsyncWSDataBackend` default instantiation."""

    fs.create_file(".env")
    backend_settings_names = [
        "CLIENT_OPTIONS",
        "LOCALE_ENCODING",
        "READ_CHUNK_SIZE",
        "URI",
        "WRITE_CHUNK_SIZE",
    ]
    for name in backend_settings_names:
        monkeypatch.delenv(f"RALPH_BACKENDS__DATA__WS__{name}", raising=False)

    assert AsyncWSDataBackend.name == "async_ws"
    assert AsyncWSDataBackend.settings_class == WSDataBackendSettings
    msg = "Failed to instantiate default async data backend settings: "
    with pytest.raises(
        BackendParameterException,
        match=msg,
    ):
        with caplog.at_level(logging.ERROR):
            AsyncWSDataBackend()

    assert "ralph.backends.data.base" == caplog.record_tuples[0][0]
    assert logging.ERROR == caplog.record_tuples[0][1]
    assert msg in caplog.record_tuples[0][2]


def test_backends_data_async_ws_instantiation_with_settings(monkeypatch):
    """Test the `AsyncWSDataBackend` instantiation with settings."""
    uri = f"ws://{WS_TEST_HOST}:{WS_TEST_PORT}"
    settings = WSDataBackendSettings(URI=uri)
    backend = AsyncWSDataBackend(settings)
    assert backend.settings.URI == TypeAdapter(AnyUrl).validate_python(uri)
    assert backend.settings.LOCALE_ENCODING == "utf8"
    assert backend.settings.READ_CHUNK_SIZE == 500
    assert backend.settings.WRITE_CHUNK_SIZE == 500

    # Test overriding default values with environment variables.
    monkeypatch.setenv("RALPH_BACKENDS__DATA__WS__READ_CHUNK_SIZE", "1")
    monkeypatch.setenv("RALPH_BACKENDS__DATA__WS__URI", "ws://foo")
    backend = AsyncWSDataBackend()
    assert backend.settings.READ_CHUNK_SIZE == 1
    assert backend.settings.URI == TypeAdapter(AnyUrl).validate_python("ws://foo")


@pytest.mark.anyio
async def test_backends_data_async_ws_status_with_error_status(ws, events, caplog):
    """Test the `AsyncWSDataBackend.status` method, given a failing websocket
    connection, should return `DataBackendStatus.ERROR` or `DataBackendStatus.AWAY`.
    """
    settings = WSDataBackendSettings(URI="ws://127.0.0.1:1")
    backend = AsyncWSDataBackend(settings)
    with caplog.at_level(logging.ERROR):
        assert await backend.status() == DataBackendStatus.ERROR

    assert (
        "ralph.backends.data.async_ws",
        logging.ERROR,
        "Failed open websocket connection for ws://127.0.0.1:1/: "
        "[Errno 111] Connect call failed ('127.0.0.1', 1)",
    ) in caplog.record_tuples

    uri = TypeAdapter(AnyUrl).validate_python(f"ws://{WS_TEST_HOST}:{WS_TEST_PORT}")
    settings = WSDataBackendSettings(URI=uri)
    backend = AsyncWSDataBackend(settings)
    assert [_ async for _ in backend.read(raw_output=False)] == events
    with caplog.at_level(logging.ERROR):
        assert await backend.status() == DataBackendStatus.AWAY

    assert (
        "ralph.backends.data.async_ws",
        logging.ERROR,
        f"Failed to Ping {str(uri)}: received 1000 (OK); then sent 1000 (OK)",
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_ws_status_with_ok_status(ws, events, caplog):
    """Test the `AsyncWSDataBackend.status` method, given a successfull websocket
    connection, should return `DataBackendStatus.OK`.
    """
    settings = WSDataBackendSettings(
        URI=f"ws://{WS_TEST_HOST}:{WS_TEST_PORT}",
        CLIENT_OPTIONS={"max_queue": 5},
    )
    backend = AsyncWSDataBackend(settings)
    assert await backend.status() == DataBackendStatus.OK

    # Test that after calling `status` we can read records:
    assert [_ async for _ in backend.read(raw_output=False)] == events


@pytest.mark.anyio
async def test_backends_data_async_ws_read_with_target(ws, events, caplog):
    """Test the `AsyncWSDataBackend.read` method, given a `target` argument, should
    produce a warning level log.
    """
    settings = WSDataBackendSettings(URI=f"ws://{WS_TEST_HOST}:{WS_TEST_PORT}")
    backend = AsyncWSDataBackend(settings)
    with caplog.at_level(logging.WARNING):
        assert await backend.read(target="ws://foo").__anext__() == events[0]

    assert (
        "ralph.backends.data.async_ws",
        logging.WARNING,
        "The `target` and `chunk_size` arguments are ignored",
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_ws_read_with_raw_output(ws, events, caplog):
    """Test the `AsyncWSDataBackend.read` method with `raw_output` set to `True`."""

    settings = WSDataBackendSettings(URI=f"ws://{WS_TEST_HOST}:{WS_TEST_PORT}")
    backend = AsyncWSDataBackend(settings)
    with caplog.at_level(logging.INFO):
        assert [_ async for _ in backend.read(raw_output=True)] == [
            f"{json.dumps(event)}\n".encode("utf8") for event in events
        ]

    assert (
        "ralph.backends.data.async_ws",
        logging.INFO,
        "Read 10 records with success",
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_ws_read_without_raw_output(ws, events, caplog):
    """Test the `AsyncWSDataBackend.read` method with `raw_output` set to `False`."""

    settings = WSDataBackendSettings(URI=f"ws://{WS_TEST_HOST}:{WS_TEST_PORT}")
    backend = AsyncWSDataBackend(settings)
    with caplog.at_level(logging.INFO):
        assert [_ async for _ in backend.read(raw_output=False)] == events

    assert (
        "ralph.backends.data.async_ws",
        logging.INFO,
        "Read 10 records with success",
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_ws_read_with_connection_failure(monkeypatch, caplog):
    """Test the `AsyncWSDataBackend.read` method with `raw_output` set to `False`."""

    settings = WSDataBackendSettings(URI="ws://foo")
    backend = AsyncWSDataBackend(settings)

    class MockClient:
        """Mock the websocket client."""

        def recv(self):
            """Mock the `WebSocketClientProtocol.recv` method raising an exception."""
            raise websockets.ConnectionClosedError(None, None)

    async def get_mock_client():
        return MockClient()

    monkeypatch.setattr(backend, "client", get_mock_client)
    msg = (
        "Failed to receive message from websocket ws://foo/: "
        "no close frame received or sent"
    )
    with pytest.raises(BackendException, match=msg):
        with caplog.at_level(logging.ERROR):
            _ = [_ async for _ in backend.read(raw_output=False)]

    assert ("ralph.backends.data.async_ws", logging.ERROR, msg) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_ws_close(ws, caplog):
    """Test the `AsyncWSDataBackend.close` method."""
    settings = WSDataBackendSettings(URI=f"ws://{WS_TEST_HOST}:{WS_TEST_PORT}")
    backend = AsyncWSDataBackend(settings)
    await backend.close()
    with caplog.at_level(logging.WARNING):
        await backend.close()

    assert (
        "ralph.backends.data.async_ws",
        logging.WARNING,
        "No backend client to close.",
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_async_ws_close_with_failure(monkeypatch, caplog):
    """Test the `AsyncWSDataBackend.close` method with a failure while closing a
    websocket connection.
    """
    settings = WSDataBackendSettings(URI="ws://foo")
    backend = AsyncWSDataBackend(settings)

    class MockClient:
        """Mock the websocket client."""

        def close(self):
            """Mock the `WebSocketClientProtocol.close` method raising an exception."""
            raise websockets.ConnectionClosedError(None, None)

    monkeypatch.setattr(backend, "_client", MockClient())
    msg = (
        "Failed to close websocket connection for ws://foo/: "
        "no close frame received or sent"
    )
    with pytest.raises(BackendException, match=re.escape(msg)):
        with caplog.at_level(logging.ERROR):
            await backend.close()

    assert (
        "ralph.backends.data.async_ws",
        logging.ERROR,
        msg,
    ) in caplog.record_tuples
