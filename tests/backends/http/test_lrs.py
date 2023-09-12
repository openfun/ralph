"""Tests for Ralph Async LRS HTTP backend."""

import asyncio
import re
from unittest.mock import AsyncMock

import pytest
from pydantic import AnyHttpUrl, parse_obj_as

from ralph.backends.http.async_lrs import AsyncLRSHTTP, HTTPBackendStatus
from ralph.backends.http.lrs import LRSHTTP
from ralph.conf import settings

lrs_settings = settings.BACKENDS.HTTP.LRS


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
    monkeypatch.setattr(AsyncLRSHTTP, method, response_mock)

    async def async_function():
        """Encapsulate the synchronous method in an asynchronous function."""
        lrs = LRSHTTP()
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
                f"`AsyncLRSHTTP.{method}` (instead of `LRSHTTP.{method}`)"
                ", or run this code outside the current event loop."
            )
        ),
    ):
        await async_function()


def test_backend_http_lrs_default_properties():
    """Test default LRS properties."""
    lrs = LRSHTTP()
    assert lrs.name == "lrs"
    assert lrs.base_url == parse_obj_as(AnyHttpUrl, lrs_settings.BASE_URL)
    assert lrs.auth == (lrs_settings.USERNAME, lrs_settings.PASSWORD)
    assert lrs.headers == lrs_settings.HEADERS
    assert lrs.status_endpoint == lrs_settings.STATUS_ENDPOINT
    assert lrs.statements_endpoint == lrs_settings.STATEMENTS_ENDPOINT


def test_backends_http_lrs_inheritence(monkeypatch):
    """Test that LRSHTTP properly inherits from AsyncLRSHTTP."""
    lrs = LRSHTTP()

    # Necessary when using anyio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Test class inheritance
    assert issubclass(lrs.__class__, AsyncLRSHTTP)

    # Test "status"
    status_mock_response = HTTPBackendStatus.OK
    status_mock = AsyncMock(return_value=status_mock_response)
    monkeypatch.setattr(AsyncLRSHTTP, "status", status_mock)
    assert lrs.status() == status_mock_response
    status_mock.assert_awaited()

    # Test "list"
    list_exception = NotImplementedError
    list_mock = AsyncMock(side_effect=list_exception)
    monkeypatch.setattr(AsyncLRSHTTP, "list", list_mock)
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

    monkeypatch.setattr(AsyncLRSHTTP, "read", read_mock)
    assert list(lrs.read(chunk_size=read_chunk_size)) == read_mock_response

    # Test "write"
    write_mock_response = 118218
    chunk_size = 17
    write_mock = AsyncMock(return_value=write_mock_response)
    monkeypatch.setattr(AsyncLRSHTTP, "write", write_mock)
    assert lrs.write(chunk_size=chunk_size) == write_mock_response
    write_mock.assert_called_with(chunk_size=chunk_size)

    loop.close()
