"""Tests for Ralph LRS HTTP backend asynchronous methods."""
import asyncio
from urllib.parse import urlparse
from uuid import uuid4
import time

import httpx
from pydantic import HttpUrl, parse_obj_as
import pytest
from pytest_httpx import HTTPXMock

from ralph.backends.http.lrs_async import LRSHTTP
from ralph.exceptions import BackendException

async def _async_gen_to_list(agen):
    return [x async for x in agen]

def test_backends_http_lrs_async_http_instantiation():
    """Test the LRS backend instantiation."""
    assert LRSHTTP.name == "lrs"

    # Test working instantiation
    fake_connection_url = parse_obj_as(HttpUrl, "http://user:password@0.0.0.0:3000")
    backend = LRSHTTP(connection_url=fake_connection_url)
    assert backend.auth == ("user", "password")

    # Test failing instantiation (missing Basic Auth credentials)
    fake_connection_url = parse_obj_as(HttpUrl, "http://0.0.0.0:3000")
    with pytest.raises(ValueError):
        backend = LRSHTTP(connection_url=fake_connection_url)


@pytest.mark.asyncio
async def test_backends_http_lrs_async_get_http_exceptions(httpx_mock: HTTPXMock):
    """Test that server errors raises BackendException."""
    fake_connection_url = parse_obj_as(HttpUrl, "http://user:password@0.0.0.0:3000")
    endpoint = "http://0.0.0.0:3000/xAPI/statements"
    backend = LRSHTTP(fake_connection_url)

    # Test status Error
    httpx_mock.add_response(status_code=404)
    with pytest.raises(BackendException):
        await _async_gen_to_list(backend.async_get_statements(endpoint))

    # with pytest.raises(BackendException): 
    # httpx_mock.add_exception(httpx.ReadTimeout("Mocking: Unable to read within timeout"))
    # await _async_gen_to_list(backend.async_get_statements(endpoint))


@pytest.mark.asyncio
async def test_backends_http_lrs_async_get_method_without_more_property(httpx_mock: HTTPXMock):
    """Test the LRS backend get method."""

    fake_connection_url = parse_obj_as(HttpUrl, "http://user:password@0.0.0.0:3000")
    endpoint_multiple = "http://0.0.0.0:3000/xAPI/statements_multiple"
    endpoint_single = "http://0.0.0.0:3000/xAPI/statements_single"
    backend = LRSHTTP(fake_connection_url)

    statements_multiple = {
        "statements": [
            {"id": str(uuid4()), "timestamp": "2022-06-22T08:31:38"},
            {"id": str(uuid4()), "timestamp": "2022-07-22T08:31:38"},
            {"id": str(uuid4()), "timestamp": "2022-08-22T08:31:38"},
        ]
    }
    statements_single = {
        "statements":{"id": str(uuid4()), "timestamp": "2022-06-22T08:31:38"}
    }

    # Mock GET response of HTTPX: Multiple statmements returned
    httpx_mock.add_response(url=endpoint_multiple, method="GET", json=statements_multiple)
    result = await _async_gen_to_list(backend.async_get_statements(endpoint_multiple))
    assert result == statements_multiple["statements"]

    # Mock GET response of HTTPX: Single statmement returned
    httpx_mock.add_response(url=endpoint_single, method="GET", json=statements_single)
    result = await _async_gen_to_list(backend.async_get_statements(endpoint_single))
    assert result == [statements_single["statements"]]

@pytest.mark.skip(reason="Performance is tested using https://github.com/openfun/lbt")
@pytest.mark.asyncio
async def test_backends_http_lrs_async_get_method_performance(httpx_mock: HTTPXMock):
    """Test that records can be fetched simultaneously."""

    fake_connection_url = parse_obj_as(HttpUrl, "http://user:password@0.0.0.0:3000")
    endpoint = "http://0.0.0.0:3000/xAPI/statements"

    statements = {
        "statements": [
            {"id": str(uuid4()), "timestamp": "2022-06-22T08:31:38"},
            {"id": str(uuid4()), "timestamp": "2022-07-22T08:31:38"},
            {"id": str(uuid4()), "timestamp": "2022-08-22T08:31:38"},
        ]
    }

    async def simulate_network_latency(request: httpx.Request):
        await asyncio.sleep(1)
        return httpx.Response(
            status_code=200, json=statements,
        )
    
    backend = LRSHTTP(fake_connection_url)

    httpx_mock.add_callback(simulate_network_latency)

    t1 = time.time()
    responses = await asyncio.gather(
        _async_gen_to_list(backend.async_get_statements(endpoint)),
        _async_gen_to_list(backend.async_get_statements(endpoint))
    )
    t2 = time.time()

    assert t2 -t1 < 2 #


@pytest.mark.asyncio
async def test_backends_http_lrs_async_get_method_with_more_property(httpx_mock: HTTPXMock):
    """Test the LRS backend get method."""

    fake_connection_url = parse_obj_as(HttpUrl, "http://user:password@0.0.0.0:3000")

    endpoint = "http://0.0.0.0:3000/xAPI/statements"
    more_endpoint = "/xAPI/statements/?pit_id=fake-pit-id"

    origin = urlparse(endpoint).scheme + "://" + urlparse(endpoint).netloc

    statements = {
        "statements": [
            {"id": str(uuid4()), "timestamp": "2022-06-22T08:31:38"},
            {"id": str(uuid4()), "timestamp": "2022-07-22T08:31:38"},
            {"id": str(uuid4()), "timestamp": "2022-08-22T08:31:38"},
        ],
        "more": more_endpoint,
    }
    more_statements = {
        "statements": [
            {"id": str(uuid4()), "timestamp": "2022-09-22T08:31:38"},
            {"id": str(uuid4()), "timestamp": "2022-10-22T08:31:38"},
            {"id": str(uuid4()), "timestamp": "2022-11-22T08:31:38"},
        ],
        "more": "",
    }

    backend = LRSHTTP(fake_connection_url)

    # Mock GET response of HTTPX
    httpx_mock.add_response(url=endpoint, method="GET", json=statements)
    httpx_mock.add_response(
        url=origin + more_endpoint, method="GET", json=more_statements
    )    
    result = await _async_gen_to_list(backend.async_get_statements(endpoint))
    assert result == statements["statements"] + more_statements["statements"]


@pytest.mark.asyncio
async def test_backends_http_lrs_async_post_method(httpx_mock: HTTPXMock):
    """Test the LRS backend post method."""

    fake_connection_url = parse_obj_as(HttpUrl, "http://user:password@0.0.0.0:3000")
    endpoint = "http://0.0.0.0:3000/xAPI/statements"

    statements = (
        {"id": str(uuid4()), "timestamp": "2022-06-22T08:31:38"},
        {"id": str(uuid4()), "timestamp": "2022-07-22T08:31:38"},
        {"id": str(uuid4()), "timestamp": "2022-09-22T08:31:38"},
        {"id": str(uuid4()), "timestamp": "2022-10-22T08:31:38"},
        {"id": str(uuid4()), "timestamp": "2022-11-22T08:31:38"},
    )
    backend = LRSHTTP(fake_connection_url)

    httpx_mock.add_response(url=endpoint, method="POST", json={"status_code": 200})

    # Single statement
    result = await backend.async_post_statements(endpoint, data=statements)
    assert result == 1

    # # Multiple statements no chunking
    result = await backend.async_post_statements(endpoint, data=statements)
    assert result == 1

    # # Multiple statements with chunking
    result = await backend.async_post_statements(endpoint, data=statements, chunk_size=2)
    assert result == 3


@pytest.mark.asyncio
async def test_backends_http_lrs_async_post_http_exceptions(httpx_mock: HTTPXMock):
    """Test that server errors raises BackendException."""
    fake_connection_url = parse_obj_as(HttpUrl, "http://user:password@0.0.0.0:3000")
    endpoint = "http://0.0.0.0:3000/xAPI/statements"
    backend = LRSHTTP(fake_connection_url)

    statements = (
        {"id": str(uuid4()), "timestamp": "2022-06-22T08:31:38"}
    )

    # Test status Error
    httpx_mock.add_response(status_code=404)
    with pytest.raises(BackendException):
        await backend.async_post_statements(endpoint, statements)


