"""Tests for Ralph LRS HTTP backend."""

import json
import logging
from urllib.parse import ParseResult, parse_qsl, urlencode, urljoin, urlparse
from uuid import uuid4

import pytest
from httpx import HTTPStatusError, RequestError
from pydantic import AnyHttpUrl
from pytest_httpx import HTTPXMock

from ralph.backends.http.base import HTTPBackendStatus
from ralph.backends.http.lrs import LRSHTTP, LRSQuery, OperationType
from ralph.conf import LRSHeaders
from ralph.exceptions import BackendException, BackendParameterException


def test_backends_http_lrs_http_instantiation():
    """Test the LRS backend instantiation."""
    assert LRSHTTP.name == "lrs"
    assert LRSHTTP.query == LRSQuery

    headers = LRSHeaders(
        X_EXPERIENCE_API_VERSION="1.0.3", CONTENT_TYPE="application/json"
    )
    backend = LRSHTTP(
        base_url="http://fake-lrs.com",
        username="user",
        password="pass",
        headers=headers,
        status_endpoint="/fake-status-endpoint",
        statements_endpoint="/xAPI/statements",
    )

    assert isinstance(backend.base_url, AnyHttpUrl)
    assert backend.auth == ("user", "pass")
    assert backend.headers.CONTENT_TYPE == "application/json"
    assert backend.headers.X_EXPERIENCE_API_VERSION == "1.0.3"
    assert backend.status_endpoint == "/fake-status-endpoint"
    assert backend.statements_endpoint == "/xAPI/statements"


def test_backends_http_lrs_status_method_with_successful_request(httpx_mock: HTTPXMock):
    """Tests the LRS backend status method returns `OK` when the request is
    successful.
    """
    base_url = "http://fake-lrs.com"
    status_endpoint = "/__heartbeat__"

    backend = LRSHTTP(
        base_url=base_url,
        username="user",
        password="pass",
        status_endpoint=status_endpoint,
    )

    # Mock GET response of HTTPX
    httpx_mock.add_response(
        url=urljoin(base_url, status_endpoint), method="GET", status_code=200
    )

    status = backend.status()
    assert status == HTTPBackendStatus.OK


def test_backends_http_lrs_status_method_with_request_error(
    httpx_mock: HTTPXMock, caplog
):
    """Tests the LRS backend status method returns `AWAY` when a `RequestError`
    exception is caught.
    """

    base_url = "http://fake-lrs.com"
    status_endpoint = "/__heartbeat__"

    backend = LRSHTTP(
        base_url=base_url,
        username="user",
        password="pass",
        status_endpoint=status_endpoint,
    )

    httpx_mock.add_exception(RequestError("Test Request Error"))

    status = backend.status()
    assert (
        "ralph.backends.http.lrs",
        logging.ERROR,
        "Unable to request the server",
    ) in caplog.record_tuples
    assert status == HTTPBackendStatus.AWAY


def test_backends_http_lrs_status_method_with_http_status_error(
    httpx_mock: HTTPXMock, caplog
):
    """Tests the LRS backend status method returns `ERROR` when an `HTTPStatusError`
    is caught.
    """

    base_url = "http://fake-lrs.com"
    status_endpoint = "/__heartbeat__"

    backend = LRSHTTP(
        base_url=base_url,
        username="user",
        password="pass",
        status_endpoint=status_endpoint,
    )

    httpx_mock.add_exception(
        HTTPStatusError("Test HTTP Status Error", request=None, response=None)
    )

    status = backend.status()
    assert (
        "ralph.backends.http.lrs",
        logging.ERROR,
        "Response raised an HTTP status of 4xx or 5xx",
    ) in caplog.record_tuples
    assert status == HTTPBackendStatus.ERROR


def test_backends_http_lrs_list_method():
    "Test the LRS backend `list` method raises a `NotImplementedError`."

    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements/"

    backend = LRSHTTP(base_url=base_url, username="user", password="pass")

    msg = (
        "LRS HTTP backend does not support `list` method, "
        "cannot list from /xAPI/statements/"
    )
    with pytest.raises(NotImplementedError, match=msg):
        backend.list(target=target)


def test_backends_http_lrs_read_method_without_target(httpx_mock: HTTPXMock):
    """Tests the LRS backend `read` method without target parameter value fetches
    statements from '/xAPI/statements' default endpoint.
    """

    base_url = "http://fake-lrs.com"

    backend = LRSHTTP(base_url=base_url, username="user", password="pass")

    statements = {
        "statements": [
            {"id": str(uuid4()), "timestamp": "2022-06-22T08:31:38"},
            {"id": str(uuid4()), "timestamp": "2022-07-22T08:31:38"},
            {"id": str(uuid4()), "timestamp": "2022-08-22T08:31:38"},
        ]
    }

    # Mock HTTPX GET
    httpx_mock.add_response(
        url=ParseResult(
            scheme=urlparse(base_url).scheme,
            netloc=urlparse(base_url).netloc,
            path=backend.statements_endpoint,
            query=urlencode({"limit": 500}),
            params="",
            fragment="",
        ).geturl(),
        method="GET",
        json=statements,
    )

    result = list(backend.read())
    assert result == statements["statements"]
    assert len(result) == 3


def test_backends_http_lrs_read_method_backend_error(httpx_mock: HTTPXMock):
    """Test the LRS backend `read` method raises a `BackendException` when the server
    returns an error.
    """

    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements/"

    backend = LRSHTTP(base_url=base_url, username="user", password="pass")

    # Mock GET response of HTTPX
    httpx_mock.add_response(
        url=ParseResult(
            scheme=urlparse(base_url).scheme,
            netloc=urlparse(base_url).netloc,
            path=target,
            query=urlencode({"limit": 500}),
            params="",
            fragment="",
        ).geturl(),
        method="GET",
        status_code=500,
    )

    with pytest.raises(BackendException, match="Failed to fetch statements."):
        list(backend.read(target=target))


def test_backends_http_lrs_read_method_without_pagination(httpx_mock: HTTPXMock):
    """Test the LRS backend `read` method when the request on the target endpoint
    returns statements without pagination."""

    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements/"

    backend = LRSHTTP(base_url=base_url, username="user", password="pass")

    statements = {
        "statements": [
            {
                "id": str(uuid4()),
                "verb": {"id": "https://w3id.org/xapi/video/verbs/played"},
                "timestamp": "2022-06-22T08:31:38",
            },
            {
                "id": str(uuid4()),
                "verb": {"id": "https://w3id.org/xapi/video/verbs/played"},
                "timestamp": "2022-07-22T08:31:38",
            },
            {
                "id": str(uuid4()),
                "verb": {"id": "https://w3id.org/xapi/video/verbs/paused"},
                "timestamp": "2022-08-22T08:31:38",
            },
        ]
    }

    # Mock GET response of HTTPX without query parameter
    params = {"limit": 500}
    httpx_mock.add_response(
        url=ParseResult(
            scheme=urlparse(base_url).scheme,
            netloc=urlparse(base_url).netloc,
            path=target,
            query=urlencode(params),
            params="",
            fragment="",
        ).geturl(),
        method="GET",
        json=statements,
    )

    # Return an iterable of dict
    result = list(backend.read(target=target, raw_output=False))
    assert result == statements["statements"]
    assert len(result) == 3

    # Return an iterable of bytes
    result = list(backend.read(target=target, raw_output=True))
    assert result == [
        bytes(json.dumps(statement), encoding="utf-8")
        for statement in statements["statements"]
    ]
    assert len(result) == 3

    # Mock GET response of HTTPX with query parameter
    query = LRSQuery(query={"verb": "https://w3id.org/xapi/video/verbs/played"})

    statements_with_query_played_verb = {
        "statements": [
            raw for raw in statements["statements"] if "played" in raw["verb"]["id"]
        ]
    }

    params.update(query.query)
    httpx_mock.add_response(
        url=ParseResult(
            scheme=urlparse(base_url).scheme,
            netloc=urlparse(base_url).netloc,
            path=target,
            query=urlencode(params),
            params="",
            fragment="",
        ).geturl(),
        method="GET",
        json=statements_with_query_played_verb,
    )
    # Return an iterable of dict
    result = list(backend.read(query=query, target=target, raw_output=False))
    assert result == statements_with_query_played_verb["statements"]
    assert len(result) == 2

    # Return an iterable of bytes
    result = list(backend.read(query=query, target=target, raw_output=True))
    assert result == [
        bytes(json.dumps(statement), encoding="utf-8")
        for statement in statements_with_query_played_verb["statements"]
    ]
    assert len(result) == 2


def test_backends_http_lrs_read_method_with_pagination(httpx_mock: HTTPXMock):
    """Test the LRS backend `read` method when the request on the target endpoint
    returns statements with pagination."""

    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements/"

    backend = LRSHTTP(base_url=base_url, username="user", password="pass")

    more_target = "/xAPI/statements/?pit_id=fake-pit-id"
    statements = {
        "statements": [
            {
                "id": str(uuid4()),
                "verb": {"id": "https://w3id.org/xapi/video/verbs/played"},
                "timestamp": "2022-06-22T08:31:38",
            },
            {
                "id": str(uuid4()),
                "verb": {"id": "https://w3id.org/xapi/video/verbs/initialized"},
                "timestamp": "2022-07-22T08:31:38",
            },
            {
                "id": str(uuid4()),
                "verb": {"id": "https://w3id.org/xapi/video/verbs/paused"},
                "timestamp": "2022-08-22T08:31:38",
            },
        ],
        "more": more_target,
    }
    more_statements = {
        "statements": [
            {
                "id": str(uuid4()),
                "verb": {"id": "https://w3id.org/xapi/video/verbs/seeked"},
                "timestamp": "2022-09-22T08:31:38",
            },
            {
                "id": str(uuid4()),
                "verb": {"id": "https://w3id.org/xapi/video/verbs/played"},
                "timestamp": "2022-10-22T08:31:38",
            },
            {
                "id": str(uuid4()),
                "verb": {"id": "https://w3id.org/xapi/video/verbs/paused"},
                "timestamp": "2022-11-22T08:31:38",
            },
        ]
    }

    # Mock GET response of HTTPX for target and "more" target without query parameter
    params = {"limit": 500}
    httpx_mock.add_response(
        url=ParseResult(
            scheme=urlparse(base_url).scheme,
            netloc=urlparse(base_url).netloc,
            path=target,
            query=urlencode(params),
            params="",
            fragment="",
        ).geturl(),
        method="GET",
        json=statements,
    )
    params.update(dict(parse_qsl(urlparse(more_target).query)))
    httpx_mock.add_response(
        url=ParseResult(
            scheme=urlparse(base_url).scheme,
            netloc=urlparse(base_url).netloc,
            path=urlparse(more_target).path,
            query=urlencode(params),
            params="",
            fragment="",
        ).geturl(),
        method="GET",
        json=more_statements,
    )

    # Return an iterable of dict
    result = list(backend.read(target=target, raw_output=False))
    assert result == statements["statements"] + more_statements["statements"]
    assert len(result) == 6

    # Return an iterable of bytes
    result = list(backend.read(target=target, raw_output=True))
    assert result == [
        bytes(json.dumps(statement), encoding="utf-8")
        for statement in statements["statements"] + more_statements["statements"]
    ]
    assert len(result) == 6

    # Mock GET response of HTTPX with query parameter
    query_params = LRSQuery(query={"verb": "https://w3id.org/xapi/video/verbs/played"})

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
    params = {"limit": 500}
    params.update(query_params.query)

    httpx_mock.add_response(
        url=ParseResult(
            scheme=urlparse(base_url).scheme,
            netloc=urlparse(base_url).netloc,
            path=target,
            query=urlencode(params),
            params="",
            fragment="",
        ).geturl(),
        method="GET",
        json=statements_with_query_played_verb,
    )
    params.update(dict(parse_qsl(urlparse(more_target).query)))

    httpx_mock.add_response(
        url=ParseResult(
            scheme=urlparse(base_url).scheme,
            netloc=urlparse(base_url).netloc,
            path=urlparse(more_target).path,
            query=urlencode(params),
            params="",
            fragment="",
        ).geturl(),
        method="GET",
        json=more_statements_with_query_played_verb,
    )

    # Return an iterable of dict
    result = list(backend.read(query=query_params, target=target, raw_output=False))
    assert (
        result
        == statements_with_query_played_verb["statements"]
        + more_statements_with_query_played_verb["statements"]
    )
    assert len(result) == 2

    # Return an iterable of bytes
    result = list(backend.read(query=query_params, target=target, raw_output=True))

    assert result == [
        bytes(json.dumps(statement), encoding="utf-8")
        for statement in statements_with_query_played_verb["statements"]
        + more_statements_with_query_played_verb["statements"]
    ]
    assert len(result) == 2


def test_backends_http_lrs_write_method_without_operation(httpx_mock: HTTPXMock):
    """Tests the LRS backend `write` method, given no operation_type should POST to
    the LRS server.
    """

    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements/"

    data = [
        {"id": str(uuid4()), "timestamp": "2022-06-22T08:31:38"},
        {"id": str(uuid4()), "timestamp": "2022-07-22T08:31:38"},
        {"id": str(uuid4()), "timestamp": "2022-08-22T08:31:38"},
    ]

    backend = LRSHTTP(base_url=base_url, username="user", password="pass")

    # Mock HTTPX POST
    httpx_mock.add_response(url=urljoin(base_url, target), method="POST", json=data)

    result = backend.write(target=target, data=data)
    assert result == len(data)


def test_backends_http_lrs_write_method_without_data():
    """Tests the LRS backend `write` method returns null when no data to write
    in the target endpoint are given.
    """

    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements/"

    backend = LRSHTTP(base_url=base_url, username="user", password="pass")

    result = backend.write(target=target, data=[])
    assert result == 0


@pytest.mark.parametrize(
    "operation_type,error_msg",
    [
        (OperationType.APPEND, "append operation type is not supported."),
        (OperationType.UPDATE, "update operation type is not supported."),
        (OperationType.DELETE, "delete operation type is not supported."),
    ],
)
def test_backends_http_lrs_write_method_with_unsupported_operation(
    operation_type, error_msg
):
    """Tests the LRS backend `write` method, given an unsupported` `operation_type`,
    should raise a `BackendParameterException`.
    """

    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements/"

    backend = LRSHTTP(base_url=base_url, username="user", password="pass")

    with pytest.raises(BackendParameterException, match=error_msg):
        backend.write(target=target, data=[b"foo"], operation_type=operation_type)


def test_backends_http_lrs_write_method_without_target(httpx_mock: HTTPXMock):
    """Tests the LRS backend `write` method without target parameter value writes
    statements to '/xAPI/statements' default endpoint."""

    base_url = "http://fake-lrs.com"

    backend = LRSHTTP(base_url=base_url, username="user", password="pass")

    data = [
        {"id": str(uuid4()), "timestamp": "2022-06-22T08:31:38"},
        {"id": str(uuid4()), "timestamp": "2022-07-22T08:31:38"},
        {"id": str(uuid4()), "timestamp": "2022-08-22T08:31:38"},
    ]

    # Mock HTTPX POST
    httpx_mock.add_response(
        url=urljoin(base_url, backend.statements_endpoint), method="POST", json=data
    )

    result = backend.write(data=data, operation_type=OperationType.CREATE)
    assert result == len(data)


def test_backends_http_lrs_write_method_with_create_or_index_operation(
    httpx_mock: HTTPXMock,
):
    """Tests the `LRSHTTP.write` method with `CREATE` or `INDEX` operation_type writes
    statements to the given target endpoint.
    """

    base_url = "http://fake-lrs.com"
    target = "/xAPI/statements"

    backend = LRSHTTP(base_url=base_url, username="user", password="pass")

    data = [
        {"id": str(uuid4()), "timestamp": "2022-06-22T08:31:38"},
        {"id": str(uuid4()), "timestamp": "2022-07-22T08:31:38"},
        {"id": str(uuid4()), "timestamp": "2022-08-22T08:31:38"},
    ]

    # Mock HTTPX POST
    httpx_mock.add_response(url=urljoin(base_url, target), method="POST", json=data)

    result = backend.write(
        target=target, data=data, operation_type=OperationType.CREATE
    )
    assert result == len(data)

    result = backend.write(target=target, data=data, operation_type=OperationType.INDEX)
    assert result == len(data)
