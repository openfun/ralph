"""Tests for Ralph Async LRS HTTP backend."""

import asyncio
import re
from unittest.mock import AsyncMock

import pytest
from pydantic import AnyHttpUrl, parse_obj_as

from ralph.backends.http.async_lrs import (
    AsyncLRSHTTPBackend,
    HTTPBackendStatus,
    LRSHeaders,
    LRSHTTPBackendSettings,
    LRSStatementsQuery,
)
from ralph.backends.http.lrs import LRSHTTPBackend


@pytest.mark.anyio
@pytest.mark.parametrize("method", ["status", "list", "write", "read"])
async def test_backend_http_lrs_in_async_setting(monkeypatch, method):
    """Test that backend returns the proper error when run in async function."""

    # Define mock responses
    if method == "read":
        read_mock_response = [{"hello": "world"}, {"save": "pandas"}]

        async def response_mock(*args, **kwargs):
            """Mock a read function."""
            # pylint: disable=invalid-name
            # pylint: disable=unused-argument
            for statement in read_mock_response:
                yield statement

    else:
        response_mock = AsyncMock(return_value=HTTPBackendStatus.OK)
    monkeypatch.setattr(AsyncLRSHTTPBackend, method, response_mock)

    async def async_function():
        """Encapsulate the synchronous method in an asynchronous function."""
        lrs = LRSHTTPBackend()
        if method == "read":
            list(getattr(lrs, method)())
        else:
            getattr(lrs, method)()

    # Check that the proper error is raised
    with pytest.raises(
        RuntimeError,
        match=re.escape(
            (
                f"This event loop is already running. You must use "
                f"`AsyncLRSHTTPBackend.{method}` (instead of `LRSHTTPBackend.{method}`)"
                ", or run this code outside the current event loop."
            )
        ),
    ):
        await async_function()


@pytest.mark.anyio
def test_backend_http_lrs_default_instantiation(
    monkeypatch, fs
):  # pylint:disable = invalid-name
    """Test the `LRSHTTPBackend` default instantiation."""
    fs.create_file(".env")
    backend_settings_names = [
        "BASE_URL",
        "USERNAME",
        "PASSWORD",
        "HEADERS",
        "STATUS_ENDPOINT",
        "STATEMENTS_ENDPOINT",
    ]
    for name in backend_settings_names:
        monkeypatch.delenv(f"RALPH_BACKENDS__HTTP__LRS__{name}", raising=False)

    assert LRSHTTPBackend.name == "lrs"
    assert LRSHTTPBackend.settings_class == LRSHTTPBackendSettings
    backend = LRSHTTPBackend()
    assert backend.query == LRSStatementsQuery
    assert backend.base_url == parse_obj_as(AnyHttpUrl, "http://0.0.0.0:8100")
    assert backend.auth == ("ralph", "secret")
    assert backend.settings.HEADERS == LRSHeaders()
    assert backend.settings.STATUS_ENDPOINT == "/__heartbeat__"
    assert backend.settings.STATEMENTS_ENDPOINT == "/xAPI/statements"


def test_backends_http_lrs_http_instantiation():
    """Test the LRS backend default instantiation."""

    headers = LRSHeaders(
        X_EXPERIENCE_API_VERSION="1.0.3", CONTENT_TYPE="application/json"
    )
    settings = LRSHTTPBackendSettings(
        BASE_URL="http://fake-lrs.com",
        USERNAME="user",
        PASSWORD="pass",
        HEADERS=headers,
        STATUS_ENDPOINT="/fake-status-endpoint",
        STATEMENTS_ENDPOINT="/xAPI/statements",
    )

    assert LRSHTTPBackend.name == "lrs"
    assert LRSHTTPBackend.settings_class == LRSHTTPBackendSettings
    backend = LRSHTTPBackend(settings)
    assert backend.query == LRSStatementsQuery
    assert isinstance(backend.base_url, AnyHttpUrl)
    assert backend.auth == ("user", "pass")
    assert backend.settings.HEADERS.CONTENT_TYPE == "application/json"
    assert backend.settings.HEADERS.X_EXPERIENCE_API_VERSION == "1.0.3"
    assert backend.settings.STATUS_ENDPOINT == "/fake-status-endpoint"
    assert backend.settings.STATEMENTS_ENDPOINT == "/xAPI/statements"


def test_backends_http_lrs_inheritence(monkeypatch):
    """Test that `LRSHTTPBackend` properly inherits from `AsyncLRSHTTPBackend`."""
    lrs = LRSHTTPBackend()

    # Necessary when using anyio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Test class inheritence
    assert issubclass(lrs.__class__, AsyncLRSHTTPBackend)

    # Test "status"
    status_mock_response = HTTPBackendStatus.OK
    status_mock = AsyncMock(return_value=status_mock_response)
    monkeypatch.setattr(AsyncLRSHTTPBackend, "status", status_mock)
    assert lrs.status() == status_mock_response
    status_mock.assert_awaited()

    # Test "list"
    list_exception = NotImplementedError
    list_mock = AsyncMock(side_effect=list_exception)
    monkeypatch.setattr(AsyncLRSHTTPBackend, "list", list_mock)
    with pytest.raises(list_exception):
        lrs.list()

    # Test "read"
    read_mock_response = [{"hello": "world"}, {"save": "pandas"}]
    read_chunk_size = 11

    async def read_mock(*args, **kwargs):
        """Mock a read function."""
        # pylint: disable=invalid-name
        # pylint: disable=unused-argument

        # For simplicity, check that parameters are passed in function
        assert kwargs["chunk_size"] == read_chunk_size
        for statement in read_mock_response:
            yield statement

    monkeypatch.setattr(AsyncLRSHTTPBackend, "read", read_mock)
    assert list(lrs.read(chunk_size=read_chunk_size)) == read_mock_response

    # Test "write"
    write_mock_response = 118218
    chunk_size = 17
    write_mock = AsyncMock(return_value=write_mock_response)
    monkeypatch.setattr(AsyncLRSHTTPBackend, "write", write_mock)
    assert lrs.write(chunk_size=chunk_size) == write_mock_response
    write_mock.assert_called_with(chunk_size=chunk_size)

    loop.close()
