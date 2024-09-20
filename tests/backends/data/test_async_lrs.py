"""Tests for Ralph LRS data backend."""

import asyncio
import datetime
import json
import logging
import re
import time
from functools import partial

import httpx
import pytest
from httpx import HTTPStatusError, RequestError
from pydantic import AnyHttpUrl, AnyUrl, TypeAdapter
from pytest_httpx import HTTPXMock

from ralph.backends.data.async_lrs import AsyncLRSDataBackend
from ralph.backends.data.base import BaseOperationType, DataBackendStatus
from ralph.backends.data.lrs import LRSDataBackend, LRSDataBackendSettings, LRSHeaders
from ralph.backends.lrs.base import LRSStatementsQuery
from ralph.exceptions import BackendException, BackendParameterException

from ...helpers import mock_statement


def test_backends_data_async_lrs_default_instantiation(monkeypatch, fs, lrs_backend):
    """Test the `LRSDataBackend` default instantiation."""
    fs.create_file(".env")
    backend_settings_names = [
        "BASE_URL",
        "USERNAME",
        "PASSWORD",
        "HEADERS",
        "LOCALE_ENCODING",
        "READ_CHUNK_SIZE",
        "STATUS_ENDPOINT",
        "STATEMENTS_ENDPOINT",
        "WRITE_CHUNK_SIZE",
    ]
    for name in backend_settings_names:
        monkeypatch.delenv(f"RALPH_BACKENDS__DATA__LRS__{name}", raising=False)

    assert AsyncLRSDataBackend.name == "async_lrs"
    assert LRSDataBackend.name == "lrs"
    backend_class = lrs_backend().__class__
    assert backend_class.settings_class == LRSDataBackendSettings
    backend = backend_class()
    assert backend.query_class == LRSStatementsQuery
    assert backend.base_url == TypeAdapter(AnyHttpUrl).validate_python(
        "http://0.0.0.0:8100"
    )
    assert backend.auth == ("ralph", "secret")
    assert backend.settings.HEADERS == LRSHeaders()
    assert backend.settings.LOCALE_ENCODING == "utf8"
    assert backend.settings.READ_CHUNK_SIZE == 500
    assert backend.settings.STATUS_ENDPOINT == "/__heartbeat__"
    assert backend.settings.STATEMENTS_ENDPOINT == "/xAPI/statements"
    assert backend.settings.WRITE_CHUNK_SIZE == 500

    # Test overriding default values with environment variables.
    monkeypatch.setenv("RALPH_BACKENDS__DATA__LRS__USERNAME", "foo")
    backend = backend_class()
    assert backend.auth == ("foo", "secret")


def test_backends_data_async_lrs_instantiation_with_settings(lrs_backend):
    """Test the LRS backend instantiation with settings."""

    headers = LRSHeaders(
        X_EXPERIENCE_API_VERSION="1.0.3", CONTENT_TYPE="application/json"
    )
    settings = LRSDataBackendSettings(
        BASE_URL="http://fake-lrs.com",
        USERNAME="user",
        PASSWORD="pass",
        HEADERS=headers,
        LOCALE_ENCODING="utf-16",
        STATUS_ENDPOINT="/fake-status-endpoint",
        STATEMENTS_ENDPOINT="/xAPI/statements",
        READ_CHUNK_SIZE=5000,
        WRITE_CHUNK_SIZE=5000,
    )

    assert AsyncLRSDataBackend.settings_class == LRSDataBackendSettings
    backend = AsyncLRSDataBackend(settings)
    assert backend.query_class == LRSStatementsQuery
    assert isinstance(backend.base_url, AnyUrl)
    assert backend.base_url.scheme.lower() in ["http", "https"]
    assert backend.auth == ("user", "pass")
    assert backend.settings.HEADERS.CONTENT_TYPE == "application/json"
    assert backend.settings.HEADERS.X_EXPERIENCE_API_VERSION == "1.0.3"
    assert backend.settings.LOCALE_ENCODING == "utf-16"
    assert backend.settings.STATUS_ENDPOINT == "/fake-status-endpoint"
    assert backend.settings.STATEMENTS_ENDPOINT == "/xAPI/statements"
    assert backend.settings.READ_CHUNK_SIZE == 5000
    assert backend.settings.WRITE_CHUNK_SIZE == 5000


@pytest.mark.anyio
async def test_backends_data_async_lrs_status_with_successful_request(
    httpx_mock: HTTPXMock, lrs_backend
):
    """Test the LRS backend status method returns `OK` when the request is
    successful.
    """
    backend: AsyncLRSDataBackend = lrs_backend()
    # Mock GET response of HTTPX
    url = "http://fake-lrs.com/__heartbeat__"
    httpx_mock.add_response(url=url, method="GET", status_code=200)
    status = await backend.status()
    assert status == DataBackendStatus.OK
    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_lrs_status_with_request_error(
    httpx_mock: HTTPXMock, lrs_backend, caplog
):
    """Test the LRS backend status method returns `AWAY` when a `RequestError`
    exception is caught.
    """
    backend: AsyncLRSDataBackend = lrs_backend()
    httpx_mock.add_exception(RequestError("Test Request Error"))
    with caplog.at_level(logging.ERROR):
        status = await backend.status()
        assert (
            f"ralph.backends.data.{backend.name}",
            logging.ERROR,
            "Unable to request the server",
        ) in caplog.record_tuples

    assert status == DataBackendStatus.AWAY
    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_lrs_status_with_http_status_error(
    httpx_mock: HTTPXMock, lrs_backend, caplog
):
    """Test the LRS backend status method returns `ERROR` when an `HTTPStatusError`
    is caught.
    """
    backend: AsyncLRSDataBackend = lrs_backend()
    exception = HTTPStatusError("Test HTTP Status Error", request=None, response=None)
    httpx_mock.add_exception(exception)
    with caplog.at_level(logging.ERROR):
        status = await backend.status()
        assert (
            f"ralph.backends.data.{backend.name}",
            logging.ERROR,
            "Response raised an HTTP status of 4xx or 5xx",
        ) in caplog.record_tuples

    assert status == DataBackendStatus.ERROR
    await backend.close()


@pytest.mark.parametrize("max_statements", [None, 2, 4, 8])
@pytest.mark.anyio
async def test_backends_data_async_lrs_read_max_statements(
    httpx_mock: HTTPXMock, max_statements: int, lrs_backend
):
    """Test the LRS backend `read` method `max_statements` argument."""
    statements = [mock_statement() for _ in range(3)]
    response = {"statements": statements, "more": "/xAPI/statements/?pit_id=pit_id"}
    more_response = {"statements": statements}
    all_statements = statements * 2

    # Mock GET response of HTTPX for target and "more" target without query parameter
    url = "http://fake-lrs.com/xAPI/statements/?limit=500"
    httpx_mock.add_response(
        url=url,
        method="GET",
        json=response,
    )
    # Given max_statements equal to two - already three statements were retrieved in the
    # first request, thus no more requests are expected.
    if not max_statements == 2:
        url = "http://fake-lrs.com/xAPI/statements/?limit=500&pit_id=pit_id"
        httpx_mock.add_response(url=url, method="GET", json=more_response)

    backend: AsyncLRSDataBackend = lrs_backend()
    result = [x async for x in backend.read(max_statements=max_statements)]
    # Assert that result is of the proper length
    assert result == all_statements[:max_statements]
    await backend.close()


@pytest.mark.anyio
@pytest.mark.parametrize("prefetch", [1, 10])
async def test_backends_data_async_lrs_read_without_target(
    prefetch: int, httpx_mock: HTTPXMock, lrs_backend
):
    """Test that the LRS backend `read` method without target parameter value fetches
    statements from '/xAPI/statements/' default endpoint.
    """
    backend: AsyncLRSDataBackend = lrs_backend()
    response = {"statements": mock_statement()}
    url = "http://fake-lrs.com/xAPI/statements/?limit=500"
    httpx_mock.add_response(url=url, method="GET", json=response)
    result = [x async for x in backend.read(prefetch=prefetch)]
    assert result == [response["statements"]]
    await backend.close()


@pytest.mark.anyio
@pytest.mark.parametrize("prefetch", [1, 10])
async def test_backends_data_async_lrs_read_backend_error(
    httpx_mock: HTTPXMock, caplog, prefetch: int, lrs_backend
):
    """Test the LRS backend `read` method raises a `BackendException` when the server
    returns an error.
    """
    backend: AsyncLRSDataBackend = lrs_backend()
    url = "http://fake-lrs.com/xAPI/statements/?limit=500"
    httpx_mock.add_response(url=url, method="GET", status_code=500)
    error = (
        "Failed to fetch statements: Server error '500 Internal Server Error' for url "
        "'http://fake-lrs.com/xAPI/statements/?limit=500'\nFor more information check: "
        "https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/500"
    )
    with pytest.raises(BackendException, match=re.escape(error)):
        with caplog.at_level(logging.ERROR):
            _ = [x async for x in backend.read(prefetch=prefetch)]

    assert (
        f"ralph.backends.data.{backend.name}",
        logging.ERROR,
        error,
    ) in caplog.record_tuples
    await backend.close()


@pytest.mark.anyio
@pytest.mark.parametrize("prefetch", [1, 10])
async def test_backends_data_async_lrs_read_without_pagination(
    httpx_mock: HTTPXMock, prefetch: int, lrs_backend
):
    """Test the LRS backend `read` method when the request on the target endpoint
    returns statements without pagination.
    """
    backend: AsyncLRSDataBackend = lrs_backend()
    statements = [
        mock_statement(verb={"id": "https://w3id.org/xapi/video/verbs/played"}),
        mock_statement(verb={"id": "https://w3id.org/xapi/video/verbs/played"}),
        mock_statement(verb={"id": "https://w3id.org/xapi/video/verbs/paused"}),
    ]
    response = {"statements": statements}

    # Mock GET response of HTTPX without query parameter
    url = "http://fake-lrs.com/xAPI/statements/?limit=500"
    httpx_mock.add_response(url=url, method="GET", json=response)

    # Return an iterable of dict
    result = [x async for x in backend.read(raw_output=False, prefetch=prefetch)]
    assert result == statements

    # Return an iterable of bytes
    result = [x async for x in backend.read(raw_output=True, prefetch=prefetch)]
    assert result == [
        f"{json.dumps(statement)}\n".encode("utf-8") for statement in statements
    ]
    await backend.close()


@pytest.mark.anyio
@pytest.mark.parametrize("prefetch", [1, 10])
async def test_backends_data_async_lrs_read_without_pagination_with_query(
    httpx_mock: HTTPXMock, prefetch: int, lrs_backend
):
    """Test the LRS backend `read` method with a query when the request on the target
    endpoint returns statements without pagination.
    """
    backend: AsyncLRSDataBackend = lrs_backend()
    verb_id = "https://w3id.org/xapi/video/verbs/played"
    query = LRSStatementsQuery(verb=verb_id)
    statements = [
        mock_statement(verb={"id": verb_id}),
        mock_statement(verb={"id": verb_id}),
    ]
    response = {"statements": statements}
    # Mock GET response of HTTPX with query parameter
    url = f"http://fake-lrs.com/xAPI/statements/?limit=500&verb={verb_id}"
    httpx_mock.add_response(url=url, method="GET", json=response)
    # Return an iterable of dict
    reader = backend.read(query=query, raw_output=False, prefetch=prefetch)
    result = [x async for x in reader]
    assert result == statements

    # Return an iterable of bytes
    reader = backend.read(query=query, raw_output=True, prefetch=prefetch)
    result = [x async for x in reader]
    assert result == [
        f"{json.dumps(statement)}\n".encode("utf-8") for statement in statements
    ]
    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_lrs_read_with_pagination(
    httpx_mock: HTTPXMock, lrs_backend
):
    """Test the LRS backend `read` method when the request on the target endpoint
    returns statements with pagination.
    """
    backend: AsyncLRSDataBackend = lrs_backend()
    statements = [
        mock_statement(verb={"id": "https://w3id.org/xapi/video/verbs/played"}),
        mock_statement(verb={"id": "https://w3id.org/xapi/video/verbs/initialized"}),
        mock_statement(verb={"id": "https://w3id.org/xapi/video/verbs/paused"}),
    ]
    more_statements = [
        mock_statement(verb={"id": "https://w3id.org/xapi/video/verbs/seeked"}),
        mock_statement(verb={"id": "https://w3id.org/xapi/video/verbs/played"}),
        mock_statement(verb={"id": "https://w3id.org/xapi/video/verbs/paused"}),
    ]
    all_statements = statements + more_statements
    response = {"statements": statements, "more": "/xAPI/statements/?pit_id=pit_id"}
    more_response = {"statements": more_statements}

    url = "http://fake-lrs.com/xAPI/statements/?limit=500"
    httpx_mock.add_response(url=url, method="GET", json=response)
    url = "http://fake-lrs.com/xAPI/statements/?limit=500&pit_id=pit_id"
    httpx_mock.add_response(url=url, method="GET", json=more_response)

    # Return an iterable of dict
    result = [x async for x in backend.read(raw_output=False)]
    assert result == all_statements

    # Return an iterable of bytes
    result = [x async for x in backend.read(raw_output=True)]
    assert result == [
        f"{json.dumps(statement)}\n".encode("utf-8") for statement in all_statements
    ]
    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_lrs_read_with_pagination_with_query(
    httpx_mock: HTTPXMock, lrs_backend
):
    """Test the LRS backend `read` method with a query when the request on the target
    endpoint returns statements with pagination.
    """
    backend: AsyncLRSDataBackend = lrs_backend()
    verb_id = "https://w3id.org/xapi/video/verbs/played"
    query = LRSStatementsQuery(verb=verb_id)
    statements = [mock_statement(verb={"id": verb_id})]
    more_statements = [
        mock_statement(verb={"id": verb_id}),
    ]
    all_statements = statements + more_statements
    response = {"statements": statements, "more": "/xAPI/statements/?pit_id=pit_id"}
    more_response = {"statements": more_statements}

    # Mock GET response of HTTPX with query parameter
    url = f"http://fake-lrs.com/xAPI/statements/?limit=500&verb={verb_id}"
    httpx_mock.add_response(url=url, method="GET", json=response)
    url = f"http://fake-lrs.com/xAPI/statements/?limit=500&verb={verb_id}&pit_id=pit_id"
    httpx_mock.add_response(url=url, method="GET", json=more_response)

    # Return an iterable of dict
    reader = backend.read(query=query, raw_output=False)
    result = [x async for x in reader]
    assert result == all_statements

    # Return an iterable of bytes
    reader = backend.read(query=query, raw_output=True)
    result = [x async for x in reader]
    assert result == [
        f"{json.dumps(statement)}\n".encode("utf-8") for statement in all_statements
    ]
    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_lrs_read_with_query_dates(
    httpx_mock: HTTPXMock, lrs_backend
):
    """Test the LRS backend `read` method with a query containing dates."""
    backend: AsyncLRSDataBackend = lrs_backend()
    verb_id = "https://w3id.org/xapi/video/verbs/played"
    since = datetime.datetime(2020, 1, 1, 0, 0)
    until = datetime.datetime(2020, 2, 1, 0, 0)
    query = LRSStatementsQuery(
        verb=verb_id,
        since=since,
        until=until,
    )
    statements = [mock_statement(verb={"id": verb_id})]
    response = {"statements": statements}

    # Mock GET response of HTTPX with query parameter
    url = (
        f"http://fake-lrs.com/xAPI/statements/?"
        "limit=500&"
        f"verb={verb_id}&"
        f"since={since.isoformat()}&"
        f"until={until.isoformat()}"
    )
    httpx_mock.add_response(url=url, method="GET", json=response)

    # Return an iterable of dict
    reader = backend.read(query=query, raw_output=False)
    result = [x async for x in reader]
    assert result == statements

    # Return an iterable of bytes
    reader = backend.read(query=query, raw_output=True)
    result = [x async for x in reader]
    assert result == [
        f"{json.dumps(statement)}\n".encode("utf-8") for statement in statements
    ]
    await backend.close()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "chunk_size,concurrency,statement_count_logs",
    [
        (500, 1, [6]),
        (2, 1, [6]),
        (500, 2, [6]),
        (2, 2, [2, 2, 2]),
        (1, 2, [1, 1, 1, 1, 1, 1]),
    ],
)
async def test_backends_data_async_lrs_write_without_operation(  # noqa: PLR0913
    httpx_mock: HTTPXMock,
    lrs_backend,
    caplog,
    chunk_size,
    concurrency,
    statement_count_logs,
):
    """Test the LRS backend `write` method, given no operation_type should POST to
    the LRS server.
    """
    backend: AsyncLRSDataBackend = lrs_backend()
    statements = [mock_statement() for _ in range(6)]

    # Mock HTTPX POST
    url = "http://fake-lrs.com/xAPI/statements/"
    httpx_mock.add_response(url=url, method="POST", json=statements)

    with caplog.at_level(logging.DEBUG):
        assert await backend.write(
            data=statements,
            chunk_size=chunk_size,
            concurrency=concurrency,
        ) == len(statements)

    # If no chunk_size is provided, a default value (500) should be used.
    if chunk_size is None:
        chunk_size = 500

    assert (
        f"ralph.backends.data.{backend.name}",
        logging.DEBUG,
        "Start writing to the http://fake-lrs.com/xAPI/statements/ endpoint "
        f"(chunk size: {chunk_size})",
    ) in caplog.record_tuples

    if isinstance(backend, AsyncLRSDataBackend):
        # Only async backends support `concurrency`.
        log_records = list(caplog.record_tuples)
        for statement_count_log in statement_count_logs:
            log_records.remove(
                (
                    f"ralph.backends.data.{backend.name}",
                    logging.DEBUG,
                    f"Posted {statement_count_log} statements",
                )
            )
    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_lrs_write_without_data(caplog, lrs_backend):
    """Test the LRS backend `write` method returns null when no data to write
    in the target endpoint are given.
    """
    backend: AsyncLRSDataBackend = lrs_backend()
    with caplog.at_level(logging.INFO):
        result = await backend.write([])

    assert (
        "ralph.backends.data.base",
        logging.INFO,
        "Data Iterator is empty; skipping write to target",
    ) in caplog.record_tuples

    assert result == 0
    await backend.close()


@pytest.mark.parametrize(
    "operation_type,error_msg",
    [
        (BaseOperationType.APPEND, "Append operation_type is not allowed"),
        (BaseOperationType.UPDATE, "Update operation_type is not allowed"),
        (BaseOperationType.DELETE, "Delete operation_type is not allowed"),
    ],
)
@pytest.mark.anyio
async def test_backends_data_async_lrs_write_with_unsupported_operation(
    lrs_backend, operation_type, caplog, error_msg
):
    """Test the LRS backend `write` method, given an unsupported` `operation_type`,
    should raise a `BackendParameterException`.
    """
    backend: AsyncLRSDataBackend = lrs_backend()
    with pytest.raises(BackendParameterException, match=error_msg):
        with caplog.at_level(logging.ERROR):
            await backend.write(data=[b"foo"], operation_type=operation_type)

    assert (
        "ralph.backends.data.base",
        logging.ERROR,
        error_msg,
    ) in caplog.record_tuples
    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_lrs_write_with_invalid_parameters(
    httpx_mock: HTTPXMock, lrs_backend, caplog
):
    """Test the LRS backend `write` method, given invalid_parameters
    should raise a `BackendParameterException`.
    """
    backend: AsyncLRSDataBackend = lrs_backend()
    if not isinstance(backend, AsyncLRSDataBackend):
        # Only async backends support `concurrency`.
        await backend.close()
        return

    error = "concurrency must be a strictly positive integer"
    with pytest.raises(BackendParameterException, match=error):
        with caplog.at_level(logging.ERROR):
            await backend.write(data=[b"foo"], concurrency=-1)

    assert (
        "ralph.backends.data.base",
        logging.ERROR,
        error,
    ) in caplog.record_tuples

    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_lrs_write_with_target(
    httpx_mock: HTTPXMock, lrs_backend, caplog
):
    """Test the LRS backend `write` method with a target parameter value writes
    statements to the target endpoint.
    """
    backend: AsyncLRSDataBackend = lrs_backend()
    data = [mock_statement() for _ in range(3)]

    # Mock HTTPX POST
    url = "http://fake-lrs.com/not-xAPI/not-statements/"
    httpx_mock.add_response(
        url=url,
        method="POST",
        json=data,
    )

    with caplog.at_level(logging.DEBUG):
        assert await backend.write(data=data, target="/not-xAPI/not-statements/") == 3

    assert (
        f"ralph.backends.data.{backend.name}",
        logging.DEBUG,
        f"Start writing to the {url} endpoint (chunk size: 500)",
    ) in caplog.record_tuples
    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_lrs_write_with_target_and_binary_data(
    httpx_mock: HTTPXMock, lrs_backend, caplog
):
    """Test the LRS backend `write` method with a target parameter value given
    binary statements, writes them to the target endpoint.
    """
    backend: AsyncLRSDataBackend = lrs_backend()
    data = [mock_statement() for _ in range(3)]
    bytes_data = [json.dumps(d).encode("utf-8") for d in data]

    # Mock HTTPX POST
    url = "http://fake-lrs.com/not-xAPI/not-statements/"
    httpx_mock.add_response(
        url=url,
        method="POST",
        json=data,
    )

    with caplog.at_level(logging.DEBUG):
        assert (
            await backend.write(data=bytes_data, target="/not-xAPI/not-statements/")
            == 3
        )

    assert (
        f"ralph.backends.data.{backend.name}",
        logging.DEBUG,
        f"Start writing to the {url} endpoint (chunk size: 500)",
    ) in caplog.record_tuples
    await backend.close()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "operation_type",
    [BaseOperationType.CREATE, BaseOperationType.INDEX],
)
async def test_backends_data_async_lrs_write_with_create_or_index_operation(
    operation_type, httpx_mock: HTTPXMock, lrs_backend, caplog
):
    """Test the `LRSHTTP.write` method with `CREATE` or `INDEX` operation_type writes
    statements to the given target endpoint.
    """
    backend: AsyncLRSDataBackend = lrs_backend()
    data = [mock_statement() for _ in range(3)]

    # Mock HTTPX POST
    url = "http://fake-lrs.com/xAPI/statements/"
    httpx_mock.add_response(url=url, method="POST", json=data)

    with caplog.at_level(logging.DEBUG):
        assert await backend.write(data=data, operation_type=operation_type) == 3

    assert (
        f"ralph.backends.data.{backend.name}",
        logging.DEBUG,
        "Posted 3 statements",
    ) in caplog.record_tuples
    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_lrs_write_with_post_exception(
    httpx_mock: HTTPXMock,
    lrs_backend,
    caplog,
):
    """Test the `LRSHTTP.write` method with HTTP error."""
    backend: AsyncLRSDataBackend = lrs_backend()
    data = [mock_statement()]

    # Mock HTTPX POST
    url = "http://fake-lrs.com/xAPI/statements/"
    httpx_mock.add_response(url=url, method="POST", json=data, status_code=500)
    with pytest.raises(BackendException):
        with caplog.at_level(logging.ERROR):
            await backend.write(data=data)

    msg = (
        "Failed to post statements: Server error '500 Internal Server Error' for url "
        "'http://fake-lrs.com/xAPI/statements/'\nFor more information check: "
        "https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/500"
    )
    assert (
        f"ralph.backends.data.{backend.name}",
        logging.ERROR,
        msg,
    ) in caplog.record_tuples

    # Given `ignore_errors=True` the `write` method should log a warning message.
    with caplog.at_level(logging.WARNING):
        assert not (await backend.write(data=data, ignore_errors=True))

    assert (
        f"ralph.backends.data.{backend.name}",
        logging.WARNING,
        msg,
    ) in caplog.record_tuples
    await backend.close()


# Asynchronicity tests for dev purposes (skip in CI)


@pytest.mark.skip(reason="Timing based tests are too unstable to run in CI.")
@pytest.mark.anyio
@pytest.mark.parametrize(
    "num_pages,chunk_size,network_latency_time", [(3, 3, 0.2), (10, 3, 0.2)]
)
async def test_backends_data_async_lrs_read_concurrency(
    httpx_mock: HTTPXMock, num_pages, chunk_size, network_latency_time, lrs_backend
):
    """Test concurrency performances in `read`, for development use.

    Args:
        num_pages: the number of pages to generate
        chunk_size: the number of results per page
        network_latency_time: the wait duration before GET results

    NB: Maximal gains are (num_pages-1)*fetch_time; when batch_processing_time >
    fetch_time
    """
    backend: AsyncLRSDataBackend = lrs_backend()
    if not isinstance(backend, AsyncLRSDataBackend):
        # Only async backends support `concurrency`.
        await backend.close()
        return

    async def _simulate_network_latency(request: httpx.Request, response):
        """Return requested statements after an async sleep time."""

        await asyncio.sleep(network_latency_time)
        return httpx.Response(status_code=200, json=response)

    async def _simulate_slow_processing():
        """Async sleep for a fixed amount of time."""
        # Time per chunk = API response time to maximize saved time
        processing_time = network_latency_time / chunk_size
        await asyncio.sleep(processing_time)

    # Generate fake targets
    targets = {0: "/xAPI/statements/"}
    for index in range(1, num_pages):
        targets[index] = f"/xAPI/statements/?pit_id=fake-pit-{index}"

    # Generate fake statements
    all_statements = {}
    for index in range(num_pages):
        all_statements[index] = {
            "statements": [mock_statement() for _ in range(chunk_size)]
        }
        if index < num_pages - 1:
            all_statements[index]["more"] = targets[index + 1]

    # Mock HTTPX GET
    for index in range(num_pages):
        pit_id = f"&pit_id=fake-pit-{index}"
        if index == 0:
            pit_id = ""
        url = f"http://fake-lrs.com/xAPI/statements/?limit={chunk_size}{pit_id}"
        statements = all_statements[index]
        httpx_mock.add_callback(
            partial(_simulate_network_latency, response=statements),
            url=url,
            method="GET",
        )

    # Check that read with `prefetch` is faster than without when processing is slow
    time_1 = time.time()
    async for _ in backend.read(target=targets[0], chunk_size=chunk_size):
        await _simulate_slow_processing()
    without_prefetch_duration = time.time() - time_1

    time_2 = time.time()
    async for _ in backend.read(target=targets[0], chunk_size=chunk_size, prefetch=100):
        await _simulate_slow_processing()
    prefetch_duration = time.time() - time_2

    # Assert gains are close enough to theoretical gains
    proximity_ratio = 0.9
    assert (
        without_prefetch_duration
        > prefetch_duration + proximity_ratio * (num_pages - 1) * network_latency_time
    )


@pytest.mark.skip(reason="Timing based tests are too unstable to run in CI")
@pytest.mark.anyio
async def test_backends_data_async_lrs_write_concurrency(
    httpx_mock: HTTPXMock, lrs_backend
):
    """Test concurrency performances in `write`, for development use."""
    backend: AsyncLRSDataBackend = lrs_backend()
    if not isinstance(backend, AsyncLRSDataBackend):
        # Only async backends support `concurrency`.
        await backend.close()
        return

    data = [mock_statement() for _ in range(6)]

    # Changing data length might break tests
    assert len(data) == 6

    # Mock HTTPX POST
    async def simulate_network_latency(_):
        await asyncio.sleep(0.5)
        return httpx.Response(status_code=200)

    httpx_mock.add_callback(simulate_network_latency)

    # Check that concurrent write is faster than non-concurrent
    time_1 = time.time()
    await backend.write(data, chunk_size=2, concurrency=1)
    non_concurrent_duration = time.time() - time_1

    time_2 = time.time()
    await backend.write(data=data, chunk_size=2, concurrency=3)
    concurrent_duration = time.time() - time_2

    # Server side processing time should be 3 times faster
    assert non_concurrent_duration > 2.1 * concurrent_duration

    # Check that write with `concurrency`=2 functions as expected
    time_1 = time.time()
    await backend.write(data=data, chunk_size=1, concurrency=2)
    limited_concurrency_duration = time.time() - time_1

    # Server side processing time should be 3 times faster with unlimited
    assert limited_concurrency_duration > 2.1 * concurrent_duration
    assert limited_concurrency_duration <= 3.1 * concurrent_duration

