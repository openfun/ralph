"""Tests for Ralph LRS HTTP backend."""

import asyncio
import json
import logging
import time
from functools import partial
from urllib.parse import ParseResult, parse_qsl, urlencode, urljoin, urlparse

import httpx
import pytest
from httpx import HTTPStatusError, RequestError
from pydantic import AnyHttpUrl, parse_obj_as
from pytest_httpx import HTTPXMock

from ralph.backends.http.async_lrs import (
    AsyncLRSHTTPBackend,
    LRSHeaders,
    LRSHTTPBackendSettings,
    LRSStatementsQuery,
    OperationType,
)
from ralph.backends.http.base import HTTPBackendStatus
from ralph.exceptions import BackendException, BackendParameterException

from ...helpers import mock_statement

# pylint: disable=too-many-lines


async def _unpack_async_generator(async_gen):
    """Unpack content of async generator into list."""
    result = []
    async for value in async_gen:
        result.append(value)
    return result


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

    assert AsyncLRSHTTPBackend.name == "async_lrs"
    assert AsyncLRSHTTPBackend.settings_class == LRSHTTPBackendSettings
    backend = AsyncLRSHTTPBackend()
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

    assert AsyncLRSHTTPBackend.name == "async_lrs"
    assert AsyncLRSHTTPBackend.settings_class == LRSHTTPBackendSettings
    backend = AsyncLRSHTTPBackend(settings)
    assert backend.query == LRSStatementsQuery
    assert isinstance(backend.base_url, AnyHttpUrl)
    assert backend.auth == ("user", "pass")
    assert backend.settings.HEADERS.CONTENT_TYPE == "application/json"
    assert backend.settings.HEADERS.X_EXPERIENCE_API_VERSION == "1.0.3"
    assert backend.settings.STATUS_ENDPOINT == "/fake-status-endpoint"
    assert backend.settings.STATEMENTS_ENDPOINT == "/xAPI/statements"


@pytest.mark.anyio
async def test_backends_http_lrs_status_with_successful_request(
    httpx_mock: HTTPXMock,
):
    """Test the LRS backend status method returns `OK` when the request is
    successful.
    """
    base_url = "http://fake-lrs.com"
    status_endpoint = "/__heartbeat__"

    settings = LRSHTTPBackendSettings(
        BASE_URL=base_url,
        USERNAME="user",
        PASSWORD="pass",
        STATUS_ENDPOINT=status_endpoint,
    )
    backend = AsyncLRSHTTPBackend(settings)

    # Mock GET response of HTTPX
    httpx_mock.add_response(
        url=urljoin(base_url, status_endpoint), method="GET", status_code=200
    )

    status = await backend.status()
    assert status == HTTPBackendStatus.OK


@pytest.mark.anyio
async def test_backends_http_lrs_status_with_request_error(
    httpx_mock: HTTPXMock, caplog
):
    """Test the LRS backend status method returns `AWAY` when a `RequestError`
    exception is caught.
    """

    base_url = "http://fake-lrs.com"
    status_endpoint = "/__heartbeat__"

    settings = LRSHTTPBackendSettings(
        BASE_URL=base_url,
        USERNAME="user",
        PASSWORD="pass",
        STATUS_ENDPOINT=status_endpoint,
    )
    backend = AsyncLRSHTTPBackend(settings)

    httpx_mock.add_exception(RequestError("Test Request Error"))

    with caplog.at_level(logging.ERROR):
        status = await backend.status()
        assert (
            "ralph.backends.http.async_lrs",
            logging.ERROR,
            "Unable to request the server",
        ) in caplog.record_tuples

    assert status == HTTPBackendStatus.AWAY


@pytest.mark.anyio
async def test_backends_http_lrs_status_with_http_status_error(
    httpx_mock: HTTPXMock, caplog
):
    """Test the LRS backend status method returns `ERROR` when an `HTTPStatusError`
    is caught.
    """

    base_url = "http://fake-lrs.com"
    status_endpoint = "/__heartbeat__"

    settings = LRSHTTPBackendSettings(
        BASE_URL=base_url,
        USERNAME="user",
        PASSWORD="pass",
        STATUS_ENDPOINT=status_endpoint,
    )
    backend = AsyncLRSHTTPBackend(settings)

    httpx_mock.add_exception(
        HTTPStatusError("Test HTTP Status Error", request=None, response=None)
    )

    with caplog.at_level(logging.ERROR):
        status = await backend.status()

        assert (
            "ralph.backends.http.async_lrs",
            logging.ERROR,
            "Response raised an HTTP status of 4xx or 5xx",
        ) in caplog.record_tuples
    assert status == HTTPBackendStatus.ERROR


@pytest.mark.anyio
async def test_backends_http_lrs_list(caplog):
    """Test the LRS backend `list` method raises a `NotImplementedError`."""

    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements/"

    settings = LRSHTTPBackendSettings(
        BASE_URL=base_url,
        USERNAME="user",
        PASSWORD="pass",
    )
    backend = AsyncLRSHTTPBackend(settings)

    msg = (
        "LRS HTTP backend does not support `list` method, "
        "cannot list from /xAPI/statements/"
    )
    with pytest.raises(NotImplementedError, match=msg):
        with caplog.at_level(logging.ERROR):
            await backend.list(target=target)

            assert (
                "ralph.backends.http.async_lrs",
                logging.ERROR,
                (
                    "LRS HTTP backend does not support `list` method, cannot list"
                    f" from {target}"
                ),
            ) in caplog.record_tuples


@pytest.mark.parametrize("max_statements", [None, 2, 4, 8])
@pytest.mark.anyio
async def test_backends_http_lrs_read_max_statements(
    httpx_mock: HTTPXMock, max_statements: int
):
    """Test the LRS backend `read` method `max_statements` property."""

    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements/"
    more_target = "/xAPI/statements/?pit_id=fake-pit-id"

    chunk_size = 3

    statements = {
        "statements": [mock_statement() for _ in range(chunk_size)],
        "more": more_target,
    }
    more_statements = {
        "statements": [mock_statement() for _ in range(chunk_size)],
    }

    # Mock GET response of HTTPX for target and "more" target without query parameter
    default_params = LRSStatementsQuery(limit=chunk_size).dict(
        exclude_none=True, exclude_unset=True
    )
    httpx_mock.add_response(
        url=ParseResult(
            scheme=urlparse(base_url).scheme,
            netloc=urlparse(base_url).netloc,
            path=target,
            query=urlencode(default_params).lower(),
            params="",
            fragment="",
        ).geturl(),
        method="GET",
        json=statements,
    )

    if (max_statements is None) or (max_statements > chunk_size):
        default_params.update(dict(parse_qsl(urlparse(more_target).query)))
        httpx_mock.add_response(
            url=ParseResult(
                scheme=urlparse(base_url).scheme,
                netloc=urlparse(base_url).netloc,
                path=urlparse(more_target).path,
                query=urlencode(default_params).lower(),
                params="",
                fragment="",
            ).geturl(),
            method="GET",
            json=more_statements,
        )

    settings = AsyncLRSHTTPBackend.settings_class(
        BASE_URL=base_url, USERNAME="user", PASSWORD="pass"
    )
    backend = AsyncLRSHTTPBackend(settings)

    # Return an iterable of dict
    result = await _unpack_async_generator(
        backend.read(
            target=target, max_statements=max_statements, chunk_size=chunk_size
        )
    )
    all_statements = statements["statements"] + more_statements["statements"]
    assert len(all_statements) == 6

    # Assert that result is of the proper length
    if max_statements is None:
        assert result == all_statements
    else:
        assert result == all_statements[:max_statements]


@pytest.mark.parametrize("greedy", [False, True])
@pytest.mark.anyio
async def test_backends_http_lrs_read_without_target(
    httpx_mock: HTTPXMock, greedy: bool
):
    """Test that the LRS backend `read` method without target parameter value fetches
    statements from '/xAPI/statements' default endpoint.
    """

    base_url = "http://fake-lrs.com"

    settings = LRSHTTPBackendSettings(
        BASE_URL=base_url,
        USERNAME="user",
        PASSWORD="pass",
    )
    backend = AsyncLRSHTTPBackend(settings)

    statements = {"statements": [mock_statement() for _ in range(3)]}

    # Mock HTTPX GET
    default_params = LRSStatementsQuery(limit=500).dict(
        exclude_none=True, exclude_unset=True
    )
    httpx_mock.add_response(
        url=ParseResult(
            scheme=urlparse(base_url).scheme,
            netloc=urlparse(base_url).netloc,
            path=backend.settings.STATEMENTS_ENDPOINT,
            query=urlencode(default_params).lower(),
            params="",
            fragment="",
        ).geturl(),
        method="GET",
        json=statements,
    )

    result = await _unpack_async_generator(backend.read(greedy=greedy))
    assert result == statements["statements"]
    assert len(result) == 3


@pytest.mark.anyio
@pytest.mark.parametrize("greedy", [False, True])
async def test_backends_http_lrs_read_backend_error(
    httpx_mock: HTTPXMock, caplog, greedy: bool
):
    """Test the LRS backend `read` method raises a `BackendException` when the server
    returns an error.
    """

    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements/"

    settings = LRSHTTPBackendSettings(
        BASE_URL=base_url,
        USERNAME="user",
        PASSWORD="pass",
    )
    backend = AsyncLRSHTTPBackend(settings)

    # Mock GET response of HTTPX
    default_params = LRSStatementsQuery(limit=500).dict(
        exclude_none=True, exclude_unset=True
    )
    httpx_mock.add_response(
        url=ParseResult(
            scheme=urlparse(base_url).scheme,
            netloc=urlparse(base_url).netloc,
            path=target,
            query=urlencode(default_params).lower(),
            params="",
            fragment="",
        ).geturl(),
        method="GET",
        status_code=500,
    )

    with pytest.raises(BackendException, match="Failed to fetch statements."):
        with caplog.at_level(logging.ERROR):
            await _unpack_async_generator(backend.read(target=target, greedy=greedy))

            assert (
                "ralph.backends.http.async_lrs",
                logging.ERROR,
                "Failed to fetch statements.",
            ) in caplog.record_tuples


@pytest.mark.anyio
@pytest.mark.parametrize("greedy", [False, True])
async def test_backends_http_lrs_read_without_pagination(
    httpx_mock: HTTPXMock, greedy: bool
):
    """Test the LRS backend `read` method when the request on the target endpoint
    returns statements without pagination."""

    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements/"

    settings = LRSHTTPBackendSettings(
        BASE_URL=base_url,
        USERNAME="user",
        PASSWORD="pass",
    )
    backend = AsyncLRSHTTPBackend(settings)

    statements = {
        "statements": [
            mock_statement(verb={"id": "https://w3id.org/xapi/video/verbs/played"}),
            mock_statement(verb={"id": "https://w3id.org/xapi/video/verbs/played"}),
            mock_statement(verb={"id": "https://w3id.org/xapi/video/verbs/paused"}),
        ]
    }

    # Mock GET response of HTTPX without query parameter
    default_params = LRSStatementsQuery(limit=500).dict(
        exclude_none=True, exclude_unset=True
    )
    httpx_mock.add_response(
        url=ParseResult(
            scheme=urlparse(base_url).scheme,
            netloc=urlparse(base_url).netloc,
            path=target,
            query=urlencode(default_params).lower(),
            params="",
            fragment="",
        ).geturl(),
        method="GET",
        json=statements,
    )

    # Return an iterable of dict
    result = await _unpack_async_generator(
        backend.read(target=target, raw_output=False, greedy=greedy)
    )
    assert result == statements["statements"]
    assert len(result) == 3

    # Return an iterable of bytes
    result = await _unpack_async_generator(
        backend.read(target=target, raw_output=True, greedy=greedy)
    )
    assert result == [
        bytes(json.dumps(statement), encoding="utf-8")
        for statement in statements["statements"]
    ]
    assert len(result) == 3

    # Mock GET response of HTTPX with query parameter
    query = LRSStatementsQuery(verb="https://w3id.org/xapi/video/verbs/played")

    statements_with_query_played_verb = {
        "statements": [
            raw for raw in statements["statements"] if "played" in raw["verb"]["id"]
        ]
    }
    query_params = query.dict(exclude_none=True, exclude_unset=True)
    query_params.update({"limit": 500})
    httpx_mock.add_response(
        url=ParseResult(
            scheme=urlparse(base_url).scheme,
            netloc=urlparse(base_url).netloc,
            path=target,
            query=urlencode(query_params).lower(),
            params="",
            fragment="",
        ).geturl(),
        method="GET",
        json=statements_with_query_played_verb,
    )
    # Return an iterable of dict
    result = await _unpack_async_generator(
        backend.read(query=query, target=target, raw_output=False, greedy=greedy)
    )
    assert result == statements_with_query_played_verb["statements"]
    assert len(result) == 2

    # Return an iterable of bytes
    result = await _unpack_async_generator(
        backend.read(query=query, target=target, raw_output=True, greedy=greedy)
    )
    assert result == [
        bytes(json.dumps(statement), encoding="utf-8")
        for statement in statements_with_query_played_verb["statements"]
    ]
    assert len(result) == 2


@pytest.mark.anyio
async def test_backends_http_lrs_read_with_pagination(httpx_mock: HTTPXMock):
    """Test the LRS backend `read` method when the request on the target endpoint
    returns statements with pagination."""

    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements/"

    settings = LRSHTTPBackendSettings(
        BASE_URL=base_url,
        USERNAME="user",
        PASSWORD="pass",
    )
    backend = AsyncLRSHTTPBackend(settings)

    more_target = "/xAPI/statements/?pit_id=fake-pit-id"
    statements = {
        "statements": [
            mock_statement(verb={"id": "https://w3id.org/xapi/video/verbs/played"}),
            mock_statement(
                verb={"id": "https://w3id.org/xapi/video/verbs/initialized"}
            ),
            mock_statement(verb={"id": "https://w3id.org/xapi/video/verbs/paused"}),
        ],
        "more": more_target,
    }
    more_statements = {
        "statements": [
            mock_statement(verb={"id": "https://w3id.org/xapi/video/verbs/seeked"}),
            mock_statement(verb={"id": "https://w3id.org/xapi/video/verbs/played"}),
            mock_statement(verb={"id": "https://w3id.org/xapi/video/verbs/paused"}),
        ]
    }

    # Mock GET response of HTTPX for target and "more" target without query parameter
    default_params = LRSStatementsQuery(limit=500).dict(
        exclude_none=True, exclude_unset=True
    )
    httpx_mock.add_response(
        url=ParseResult(
            scheme=urlparse(base_url).scheme,
            netloc=urlparse(base_url).netloc,
            path=target,
            query=urlencode(default_params).lower(),
            params="",
            fragment="",
        ).geturl(),
        method="GET",
        json=statements,
    )
    default_params.update(dict(parse_qsl(urlparse(more_target).query)))
    httpx_mock.add_response(
        url=ParseResult(
            scheme=urlparse(base_url).scheme,
            netloc=urlparse(base_url).netloc,
            path=urlparse(more_target).path,
            query=urlencode(default_params).lower(),
            params="",
            fragment="",
        ).geturl(),
        method="GET",
        json=more_statements,
    )

    # Return an iterable of dict
    result = await _unpack_async_generator(
        backend.read(target=target, raw_output=False)
    )
    assert result == statements["statements"] + more_statements["statements"]
    assert len(result) == 6

    # Return an iterable of bytes
    result = await _unpack_async_generator(backend.read(target=target, raw_output=True))
    assert result == [
        bytes(json.dumps(statement), encoding="utf-8")
        for statement in statements["statements"] + more_statements["statements"]
    ]
    assert len(result) == 6

    # Mock GET response of HTTPX with query parameter
    query = LRSStatementsQuery(verb="https://w3id.org/xapi/video/verbs/played")

    statements_with_query_played_verb = {
        "statements": [
            raw for raw in statements["statements"] if "played" in raw["verb"]["id"]
        ],
        "more": more_target,
    }
    more_statements_with_query_played_verb = {
        "statements": [
            raw
            for raw in more_statements["statements"]
            if "played" in raw["verb"]["id"]
        ]
    }
    query_params = query.dict(exclude_none=True, exclude_unset=True)
    query_params.update({"limit": 500})
    httpx_mock.add_response(
        url=ParseResult(
            scheme=urlparse(base_url).scheme,
            netloc=urlparse(base_url).netloc,
            path=target,
            query=urlencode(query_params).lower(),
            params="",
            fragment="",
        ).geturl(),
        method="GET",
        json=statements_with_query_played_verb,
    )
    query_params.update(dict(parse_qsl(urlparse(more_target).query)))
    httpx_mock.add_response(
        url=ParseResult(
            scheme=urlparse(base_url).scheme,
            netloc=urlparse(base_url).netloc,
            path=urlparse(more_target).path,
            query=urlencode(query_params).lower(),
            params="",
            fragment="",
        ).geturl(),
        method="GET",
        json=more_statements_with_query_played_verb,
    )

    # Return an iterable of dict

    result = await _unpack_async_generator(
        backend.read(query=query, target=target, raw_output=False)
    )
    assert (
        result
        == statements_with_query_played_verb["statements"]
        + more_statements_with_query_played_verb["statements"]
    )
    assert len(result) == 2

    # Return an iterable of bytes
    result = await _unpack_async_generator(
        backend.read(query=query, target=target, raw_output=True)
    )

    assert result == [
        bytes(json.dumps(statement), encoding="utf-8")
        for statement in statements_with_query_played_verb["statements"]
        + more_statements_with_query_played_verb["statements"]
    ]
    assert len(result) == 2


@pytest.mark.anyio
@pytest.mark.parametrize(
    "chunk_size,simultaneous,max_num_simultaneous",
    [
        (None, False, None),
        (500, False, None),
        (2, False, None),
        (500, True, 1),
        (2, True, 1),
        (500, True, 2),
        (2, True, 2),
        (500, True, None),
        (2, True, None),
    ],
)
async def test_backends_http_lrs_write_without_operation(
    httpx_mock: HTTPXMock, caplog, chunk_size, simultaneous, max_num_simultaneous
):
    """Test the LRS backend `write` method, given no operation_type should POST to
    the LRS server.
    """

    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements/"

    data = [mock_statement() for _ in range(6)]

    settings = LRSHTTPBackendSettings(
        BASE_URL=base_url,
        USERNAME="user",
        PASSWORD="pass",
    )
    backend = AsyncLRSHTTPBackend(settings)

    # Mock HTTPX POST
    httpx_mock.add_response(url=urljoin(base_url, target), method="POST", json=data)

    with caplog.at_level(logging.DEBUG):
        result = await backend.write(
            target=target,
            data=data,
            chunk_size=chunk_size,
            simultaneous=simultaneous,
            max_num_simultaneous=max_num_simultaneous,
        )

    assert (
        "ralph.backends.http.async_lrs",
        logging.DEBUG,
        f"Start writing to the {base_url}{target} endpoint (chunk size: "
        f"{chunk_size})",
    ) in caplog.record_tuples

    assert (
        "ralph.backends.http.async_lrs",
        logging.DEBUG,
        f"Posted {len(data)} statements",
    ) in caplog.record_tuples

    assert result == len(data)


@pytest.mark.anyio
async def test_backends_http_lrs_write_without_data(caplog):
    """Test the LRS backend `write` method returns null when no data to write
    in the target endpoint are given.
    """

    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements/"

    settings = LRSHTTPBackendSettings(
        BASE_URL=base_url,
        USERNAME="user",
        PASSWORD="pass",
    )
    backend = AsyncLRSHTTPBackend(settings)

    with caplog.at_level(logging.INFO):
        result = await backend.write(target=target, data=[])

        assert (
            "ralph.backends.http.async_lrs",
            logging.INFO,
            "Data Iterator is empty; skipping write to target.",
        ) in caplog.record_tuples

    assert result == 0


@pytest.mark.parametrize(
    "operation_type,error_msg",
    [
        (OperationType.APPEND, "append operation type is not supported."),
        (OperationType.UPDATE, "update operation type is not supported."),
        (OperationType.DELETE, "delete operation type is not supported."),
    ],
)
@pytest.mark.anyio
async def test_backends_http_lrs_write_with_unsupported_operation(
    operation_type, caplog, error_msg
):
    """Test the LRS backend `write` method, given an unsupported` `operation_type`,
    should raise a `BackendParameterException`.
    """

    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements/"

    settings = LRSHTTPBackendSettings(
        BASE_URL=base_url,
        USERNAME="user",
        PASSWORD="pass",
    )
    backend = AsyncLRSHTTPBackend(settings)

    with pytest.raises(BackendParameterException, match=error_msg):
        with caplog.at_level(logging.ERROR):
            await backend.write(
                target=target, data=[b"foo"], operation_type=operation_type
            )

        assert (
            "ralph.backends.http.async_lrs",
            logging.DEBUG,
            f"{operation_type.value} operation type is not supported.",
        ) in caplog.record_tuples


@pytest.mark.parametrize(
    "simultaneous,max_num_simultaneous,error_msg",
    [
        (True, 0, "max_num_simultaneous must be a strictly positive integer"),
        (False, 2, "max_num_simultaneous can only be used with `simultaneous=True`"),
    ],
)
@pytest.mark.anyio
async def test_backends_http_lrs_write_with_invalid_parameters(
    caplog, simultaneous, max_num_simultaneous, error_msg
):
    """Test the LRS backend `write` method, given invalid_parameters
    should raise a `BackendParameterException`.
    """

    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements/"

    settings = LRSHTTPBackendSettings(
        BASE_URL=base_url,
        USERNAME="user",
        PASSWORD="pass",
    )
    backend = AsyncLRSHTTPBackend(settings)

    with pytest.raises(BackendParameterException, match=error_msg):
        with caplog.at_level(logging.ERROR):
            await backend.write(
                target=target,
                data=[b"foo"],
                simultaneous=simultaneous,
                max_num_simultaneous=max_num_simultaneous,
            )

            assert (
                "ralph.backends.http.async_lrs",
                logging.ERROR,
                error_msg,
            ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_http_lrs_write_without_target(httpx_mock: HTTPXMock, caplog):
    """Test the LRS backend `write` method without target parameter value writes
    statements to '/xAPI/statements' default endpoint."""

    base_url = "http://fake-lrs.com"

    settings = LRSHTTPBackendSettings(
        BASE_URL=base_url,
        USERNAME="user",
        PASSWORD="pass",
    )
    backend = AsyncLRSHTTPBackend(settings)

    data = [mock_statement() for _ in range(3)]

    # Mock HTTPX POST
    httpx_mock.add_response(
        url=urljoin(base_url, backend.settings.STATEMENTS_ENDPOINT),
        method="POST",
        json=data,
    )

    with caplog.at_level(logging.DEBUG):
        result = await backend.write(data=data, operation_type=OperationType.CREATE)
        assert (
            "ralph.backends.http.async_lrs",
            logging.DEBUG,
            "Start writing to the "
            f"{base_url}{LRSHTTPBackendSettings().STATEMENTS_ENDPOINT} "
            "endpoint (chunk size: 500)",
        ) in caplog.record_tuples

    assert result == len(data)


@pytest.mark.anyio
async def test_backends_http_lrs_write_with_create_or_index_operation(
    httpx_mock: HTTPXMock, caplog
):
    """Test the `LRSHTTP.write` method with `CREATE` or `INDEX` operation_type writes
    statements to the given target endpoint.
    """

    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements"

    settings = LRSHTTPBackendSettings(
        BASE_URL=base_url,
        USERNAME="user",
        PASSWORD="pass",
    )
    backend = AsyncLRSHTTPBackend(settings)

    data = [mock_statement() for _ in range(3)]

    # Mock HTTPX POST
    httpx_mock.add_response(url=urljoin(base_url, target), method="POST", json=data)

    with caplog.at_level(logging.INFO):
        result = await backend.write(
            target=target, data=data, operation_type=OperationType.CREATE
        )
    assert result == len(data)

    with caplog.at_level(logging.INFO):
        result = await backend.write(
            target=target, data=data, operation_type=OperationType.INDEX
        )
    assert result == len(data)


@pytest.mark.anyio
async def test_backends_http_lrs_write_backend_exception(
    httpx_mock: HTTPXMock,
    caplog,
):
    """Test the `LRSHTTP.write` method with HTTP error"""
    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements"

    settings = LRSHTTPBackendSettings(
        BASE_URL=base_url,
        USERNAME="user",
        PASSWORD="pass",
    )
    backend = AsyncLRSHTTPBackend(settings)

    data = [mock_statement()]

    # Mock HTTPX POST
    httpx_mock.add_response(
        url=urljoin(base_url, target), method="POST", json=data, status_code=500
    )
    with pytest.raises(BackendException):
        with caplog.at_level(logging.ERROR):
            await backend.write(target=target, data=data)
            assert (
                "ralph.backends.http.async_lrs",
                logging.ERROR,
                "Failed to post statements",
            ) in caplog.record_tuples


# Asynchronicity tests for dev purposes (skip in CI)


@pytest.mark.skip(reason="Timing based tests are too unstable to run in CI.")
@pytest.mark.anyio
@pytest.mark.parametrize(
    "num_pages,chunk_size,network_latency_time", [(3, 3, 0.2), (10, 3, 0.2)]
)
async def test_backends_http_lrs_read_concurrency(
    httpx_mock: HTTPXMock, num_pages, chunk_size, network_latency_time
):
    """Test concurrency performances in `read`, for development use.

    Args:
        num_pages: the number of pages to generate
        chunk_size: the number of results per page
        network_latency_time: the wait duration before GET results

    NB: Maximal gains are (num_pages-1)*fetch_time; when batch_processing_time >
    fetch_time
    """
    # pylint: disable=too-many-locals

    async def _simulate_network_latency(request: httpx.Request, response):
        """Return requested statements after an async sleep time."""
        # pylint: disable=unused-argument
        await asyncio.sleep(network_latency_time)
        return httpx.Response(status_code=200, json=response)

    async def _simulate_slow_processing():
        """Async sleep for a fixed amount of time."""
        # Time per chunk = API response time to maximize saved time
        processing_time = network_latency_time / chunk_size
        await asyncio.sleep(processing_time)

    base_url = "http://fake-lrs.com"

    # Generate fake targets
    target_template = "/xAPI/statements/?pit_id=fake-pit-{}"
    targets = {0: "/xAPI/statements/"}
    for index in range(1, num_pages):
        targets[index] = target_template.format(index)

    # Generate fake statements
    all_statements = {}
    for index in range(num_pages):
        all_statements[index] = {
            "statements": [mock_statement() for _ in range(chunk_size)]
        }
        if index < num_pages - 1:
            all_statements[index]["more"] = targets[index + 1]

    settings = LRSHTTPBackendSettings(
        BASE_URL=base_url,
        USERNAME="user",
        PASSWORD="pass",
    )
    backend = AsyncLRSHTTPBackend(settings)

    # Mock HTTPX GET
    params = {"limit": chunk_size}
    for index in range(num_pages):
        url = ParseResult(
            scheme=urlparse(base_url).scheme,
            netloc=urlparse(base_url).netloc,
            path=urlparse(targets[index]).path,
            query=urlencode(params),
            params="",
            fragment="",
        ).geturl()

        statements = all_statements[index]
        httpx_mock.add_callback(
            partial(_simulate_network_latency, response=statements),
            url=url,
            method="GET",
        )

        if index < num_pages - 1:
            params.update(dict(parse_qsl(urlparse(targets[index + 1]).query)))

    # Check that greedy read is faster than non-greedy when processing is slow
    time_1 = time.time()
    counter = 0
    async for _ in backend.read(target=targets[0], chunk_size=chunk_size, greedy=False):
        await _simulate_slow_processing()
        counter += 1
    duration_non_greedy = time.time() - time_1

    time_2 = time.time()
    async for _ in backend.read(target=targets[0], chunk_size=chunk_size, greedy=True):
        await _simulate_slow_processing()
    duration_greedy = time.time() - time_2

    # Assert gains are close enough to theoretical gains
    proximity_ratio = 0.9
    assert (
        duration_non_greedy
        > duration_greedy + proximity_ratio * (num_pages - 1) * network_latency_time
    )


@pytest.mark.skip(reason="Timing based tests are too unstable to run in CI")
@pytest.mark.anyio
async def test_backends_http_lrs_write_concurrency(
    httpx_mock: HTTPXMock,
):
    """Test concurrency performances in `write`, for development use."""

    base_url = "http://fake-lrs.com"

    data = [mock_statement() for _ in range(6)]

    # Changing data length might break tests
    assert len(data) == 6

    settings = LRSHTTPBackendSettings(
        BASE_URL=base_url,
        USERNAME="user",
        PASSWORD="pass",
    )
    backend = AsyncLRSHTTPBackend(settings)

    # Mock HTTPX POST
    async def simulate_network_latency(request: httpx.Request):
        # pylint: disable=unused-argument
        await asyncio.sleep(0.5)
        return httpx.Response(
            status_code=200,
        )

    httpx_mock.add_callback(simulate_network_latency)

    # Check that simultaneous write is faster than non-simultaneous
    time_1 = time.time()
    await backend.write(
        data=data,
        chunk_size=2,
        simultaneous=False,
        max_num_simultaneous=None,
    )
    duration_non_simultaneous = time.time() - time_1

    time_2 = time.time()
    await backend.write(
        data=data,
        chunk_size=2,
        simultaneous=True,
        max_num_simultaneous=None,
    )
    duration_simultaneous = time.time() - time_2

    # Server side processing time should be 3 times faster
    assert duration_non_simultaneous > 2.1 * duration_simultaneous

    # Check that write with max_num_simultaneous functions as expected
    time_1 = time.time()
    await backend.write(
        data=data,
        chunk_size=1,
        simultaneous=True,
        max_num_simultaneous=2,
    )
    duration_limited_simultaneous = time.time() - time_1

    time_2 = time.time()
    await backend.write(
        data=data,
        chunk_size=1,
        simultaneous=True,
        max_num_simultaneous=None,
    )
    duration_unlimited_simultaneous = time.time() - time_2

    # Server side processing time should be 3 times faster with unlimited
    assert duration_limited_simultaneous > 2.1 * duration_unlimited_simultaneous
    assert duration_limited_simultaneous <= 3.1 * duration_unlimited_simultaneous
