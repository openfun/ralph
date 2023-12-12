"""Tests for Ralph ldp data backend."""

import gzip
import json
import logging
import os.path
from collections.abc import Iterable
from operator import itemgetter
from xmlrpc.client import gzip_decode

import ovh
import pytest
import requests
import requests_mock

from ralph.backends.data.base import DataBackendStatus
from ralph.backends.data.ldp import LDPDataBackend
from ralph.conf import settings
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import now


def test_backends_data_ldp_default_instantiation(monkeypatch, fs):
    """Test the `LDPDataBackend` default instantiation."""

    fs.create_file(".env")
    backend_settings_names = [
        "APPLICATION_KEY",
        "APPLICATION_SECRET",
        "CONSUMER_KEY",
        "DEFAULT_STREAM_ID",
        "ENDPOINT",
        "SERVICE_NAME",
        "READ_CHUNK_SIZE",
        "REQUEST_TIMEOUT",
        "WRITE_CHUNK_SIZE",
    ]
    for name in backend_settings_names:
        monkeypatch.delenv(f"RALPH_BACKENDS__DATA__LDP__{name}", raising=False)

    assert LDPDataBackend.name == "ldp"
    assert LDPDataBackend.query_class == str
    backend = LDPDataBackend()
    assert isinstance(backend.client, ovh.Client)
    assert backend.service_name is None
    assert backend.stream_id is None
    assert backend.timeout is None

    # Test overriding default values with environment variables.
    monkeypatch.setenv("RALPH_BACKENDS__DATA__LDP__SERVICE_NAME", "foo")
    backend = LDPDataBackend()
    assert backend.service_name == "foo"
    assert backend.settings.READ_CHUNK_SIZE == 4096
    assert backend.settings.WRITE_CHUNK_SIZE == 500


def test_backends_data_ldp_instantiation_with_settings(ldp_backend):
    """Test the `LDPDataBackend` instantiation with settings."""
    backend = ldp_backend()
    assert isinstance(backend.client, ovh.Client)
    assert backend.service_name == "foo"
    assert backend.stream_id == "bar"
    assert backend.settings.READ_CHUNK_SIZE == 500
    assert backend.settings.WRITE_CHUNK_SIZE == 499

    try:
        ldp_backend(service_name="bar")
    except Exception as err:  # noqa: BLE001
        pytest.fail(f"LDPDataBackend should not raise exceptions: {err}")


@pytest.mark.parametrize(
    "exception_class",
    [ovh.exceptions.HTTPError, ovh.exceptions.InvalidResponse],
)
def test_backends_data_ldp_status_with_error_status(
    exception_class, ldp_backend, monkeypatch
):
    """Test the `LDPDataBackend.status` method, given a failed request to OVH's archive
    endpoint, should return `DataBackendStatus.ERROR`.
    """

    def mock_get(_):
        """Mock the ovh.Client get method always raising an exception."""
        raise exception_class()

    def mock_get_archive_endpoint():
        """Mock the `get_archive_endpoint` method always raising an exception."""
        raise BackendParameterException()

    backend = ldp_backend()
    monkeypatch.setattr(backend.client, "get", mock_get)
    assert backend.status() == DataBackendStatus.ERROR
    monkeypatch.setattr(backend, "_get_archive_endpoint", mock_get_archive_endpoint)
    assert backend.status() == DataBackendStatus.ERROR


def test_backends_data_ldp_status_with_ok_status(ldp_backend, monkeypatch):
    """Test the `LDPDataBackend.status` method, given a successful request to OVH's
    archive endpoint, the `status` method should return `DataBackendStatus.OK`.
    """

    def mock_get(_):
        """Mock the ovh.Client get method always returning an empty list."""
        return []

    backend = ldp_backend()
    monkeypatch.setattr(backend.client, "get", mock_get)
    assert backend.status() == DataBackendStatus.OK


def test_backends_data_ldp_list_with_invalid_target(ldp_backend):
    """Test the `LDPDataBackend.list` method given no default `stream_id` and no target
    argument should raise a `BackendParameterException`.
    """

    backend = ldp_backend(stream_id=None)
    error = "LDPDataBackend requires to set both service_name and stream_id"
    with pytest.raises(BackendParameterException, match=error):
        list(backend.list())


@pytest.mark.parametrize(
    "exception_class",
    [ovh.exceptions.HTTPError, ovh.exceptions.InvalidResponse],
)
def test_backends_data_ldp_list_failure(exception_class, ldp_backend, monkeypatch):
    """Test the `LDPDataBackend.list` method, given a failed OVH API request should
    raise a `BackendException`.
    """

    def mock_get_list_failure(_):
        """Mock the ovh.Client get method always raising an exception."""
        raise exception_class("OVH Error")

    backend = ldp_backend()
    monkeypatch.setattr(backend.client, "get", mock_get_list_failure)
    msg = r"Failed to get archives list: OVH Error"
    with pytest.raises(BackendException, match=msg):
        list(backend.list())

    def mock_get_details_failure(url):
        """Mock the ovh.Client get method raising an exception when retrieving archive
        details.
        """
        # list request
        if url.endswith("archive"):
            return ["archive_1"]
        # details request
        raise exception_class("OVH Error")

    monkeypatch.setattr(backend.client, "get", mock_get_details_failure)
    msg = r"Failed to get 'archive_1' archive details: OVH Error"
    with pytest.raises(BackendException, match=msg):
        list(backend.list(details=True))


@pytest.mark.parametrize(
    "archives,target,expected_stream_id",
    [
        # Given no archives at the OVH's archive endpoint and no `target`,
        # the `list` method should use the default `stream_id` target and yield nothing.
        ([], None, "bar"),
        # Given one archive at the OVH's archive endpoint and no `target`, the `list`
        # method should use the default `stream_id` target yield the archive.
        (["archive_1"], None, "bar"),
        # Given one archive at the OVH's archive endpoint and a `target`, the `list`
        # method should use the provided `stream_id` target yield the archive.
        (["archive_1"], "foo", "foo"),
        # Given some archives at the OVH's archive endpoint and no `target`, the `list`
        # method should use the default `stream_id` target yield the archives.
        (["archive_1", "archive_2"], None, "bar"),
    ],
)
def test_backends_data_ldp_list_without_history(
    archives, target, expected_stream_id, ldp_backend, monkeypatch
):
    """Test the `LDPDataBackend.list` method without history."""

    def mock_get(url):
        """Mock the OVH client get request."""
        assert expected_stream_id in url
        return archives

    backend = ldp_backend()
    monkeypatch.setattr(backend.client, "get", mock_get)
    result = backend.list(target)
    assert isinstance(result, Iterable)
    assert list(result) == archives


@pytest.mark.parametrize(
    "archives,target,expected_stream_id",
    [
        # Given no archives at the OVH's archive endpoint and no `target`,
        # the `list` method should use the default `stream_id` target and yield nothing.
        ([], None, "bar"),
        # Given one archive at the OVH's archive endpoint and no `target`, the `list`
        # method should use the default `stream_id` target yield the archive.
        (["archive_1"], None, "bar"),
        # Given one archive at the OVH's archive endpoint and a `target`, the `list`
        # method should use the provided `stream_id` target yield the archive.
        (["archive_1"], "foo", "foo"),
        # Given some archives at the OVH's archive endpoint and no `target`, the `list`
        # method should use the default `stream_id` target yield the archives.
        (["archive_1", "archive_2"], None, "bar"),
    ],
)
def test_backends_data_ldp_list_with_details(
    archives, target, expected_stream_id, ldp_backend, monkeypatch
):
    """Test the `LDPDataBackend.list` method with `details` set to `True`."""
    details_responses = [
        {
            "archiveId": archive,
            "createdAt": "2020-06-18T04:38:59.436634+02:00",
            "filename": "2020-06-18.gz",
            "md5": "01585b394be0495e38dbb60b20cb40a9",
            "retrievalDelay": 0,
            "retrievalState": "sealed",
            "sha256": "645d8e21e6fdb8aa7ffc5c[...]9ce612d06df8dcf67cb29a45ca",
            "size": 67906662,
        }
        for archive in archives
    ]

    get_details_response = (response for response in details_responses)

    def mock_get(url):
        """Mock the OVH client get request."""
        assert expected_stream_id in url
        # list request
        if url.endswith("archive"):
            return archives
        # details request
        return next(get_details_response)

    backend = ldp_backend()
    monkeypatch.setattr(backend.client, "get", mock_get)

    result = backend.list(target, details=True)
    assert isinstance(result, Iterable)
    assert list(result) == details_responses


@pytest.mark.parametrize("target,expected_stream_id", [(None, "bar"), ("baz", "baz")])
def test_backends_data_ldp_list_with_history(
    target, expected_stream_id, ldp_backend, monkeypatch, settings_fs
):
    """Test the `LDPDataBackend.list` method with history."""

    def mock_get(url):
        """Mock the OVH client get request."""
        assert expected_stream_id in url
        return ["archive_1", "archive_2", "archive_3"]

    backend = ldp_backend()
    monkeypatch.setattr(backend.client, "get", mock_get)

    # Given an empty history and `new` set to `True`, the `list` method should yield all
    # archives.
    expected = ["archive_1", "archive_2", "archive_3"]
    result = backend.list(target, new=True)
    assert isinstance(result, Iterable)
    assert sorted(result) == expected

    # Add archive_1 to history
    backend.history.append(
        {
            "backend": "ldp",
            "action": "read",
            "id": "archive_1",
            "filename": "2020-10-07.gz",
            "size": 23424233,
            "timestamp": "2020-10-07T16:37:25.887664+00:00",
        }
    )

    # Given a history containing one matching archive and `new` set to `True`, the
    # `list` method should yield all archives except the matching one.
    expected = ["archive_2", "archive_3"]
    result = backend.list(target, new=True)
    assert isinstance(result, Iterable)
    assert sorted(result) == expected

    # Add archive_2 to history
    backend.history.append(
        {
            "backend": "ldp",
            "action": "read",
            "id": "archive_2",
            "filename": "2020-10-07.gz",
            "size": 23424233,
            "timestamp": "2020-10-07T16:37:25.887664+00:00",
        }
    )

    # Given a history containing two matching archives and `new` set to `True`, the
    # `list` method should yield all archives except the matching ones.
    expected = ["archive_3"]
    result = backend.list(target, new=True)
    assert isinstance(result, Iterable)
    assert sorted(result) == expected

    # Add archive_3 to history
    backend.history.append(
        {
            "backend": "ldp",
            "action": "read",
            "id": "archive_3",
            "filename": "2020-10-07.gz",
            "size": 23424233,
            "timestamp": "2020-10-07T16:37:25.887664+00:00",
        }
    )

    # Given a history containing all matching archives and `new` set to `True`, the
    # `list` method should yield nothing.
    expected = []
    result = backend.list(target, new=True)
    assert isinstance(result, Iterable)
    assert sorted(result) == expected


@pytest.mark.parametrize("target,expected_stream_id", [(None, "bar"), ("baz", "baz")])
def test_backends_data_ldp_list_with_history_and_details(
    target, expected_stream_id, ldp_backend, monkeypatch, settings_fs
):
    """Test the `LDPDataBackend.list` method with a history and detailed output."""

    details_responses = [
        {
            "archiveId": "archive_1",
            "createdAt": "2020-06-18T04:38:59.436634+02:00",
            "filename": "2020-06-16.gz",
            "md5": "01585b394be0495e38dbb60b20cb40a9",
            "retrievalDelay": 0,
            "retrievalState": "sealed",
            "sha256": "645d8e21e6fdb8aa7ffc5c[...]9ce612d06df8dcf67cb29a45ca",
            "size": 67906662,
        },
        {
            "archiveId": "archive_2",
            "createdAt": "2020-06-18T04:38:59.436634+02:00",
            "filename": "2020-06-18.gz",
            "md5": "01585b394be0495e38dbb60b20cb40a9",
            "retrievalDelay": 0,
            "retrievalState": "sealed",
            "sha256": "645d8e21e6fdb8aa7ffc5c[...]9ce612d06df8dcf67cb29a45ca",
            "size": 67906662,
        },
        {
            "archiveId": "archive_3",
            "createdAt": "2020-06-19T04:38:59.436634+02:00",
            "filename": "2020-06-19.gz",
            "md5": "01585b394be0495e38dbb60b20cb40a9",
            "retrievalDelay": 0,
            "retrievalState": "sealed",
            "sha256": "645d8e21e6fdb8aa7ffc5c[...]9ce612d06df8dcf67cb29a45ca",
            "size": 67906662,
        },
    ]

    get_details_response = (response for response in details_responses)

    def mock_get(url):
        """Mock the OVH client get request."""
        assert expected_stream_id in url
        # list request
        if url.endswith("archive"):
            return ["archive_1", "archive_2", "archive_3"]
        # details request
        return next(get_details_response)

    backend = ldp_backend()
    monkeypatch.setattr(backend.client, "get", mock_get)

    # Given an empty history and `new` and `details` set to `True`, the `list` method
    # should yield all archives with additional details.
    expected = details_responses
    result = backend.list(target, details=True, new=True)
    assert isinstance(result, Iterable)
    assert sorted(result, key=itemgetter("archiveId")) == expected

    # Add archive_1 to history
    backend.history.append(
        {
            "backend": "ldp",
            "action": "read",
            "id": "archive_1",
            "filename": "2020-06-16.gz",
            "size": 23424233,
            "timestamp": "2020-10-07T16:37:25.887664+00:00",
        }
    )

    # We expect two requests to retrieve details for archive 2 and 3.
    get_details_response = (response for response in details_responses[1:])

    # Given a history containing one matching archive and `new` and `details` set to
    # `True`, the `list` method should yield all archives in the directory with
    # additional details, except the matching one.
    expected = [details_responses[1], details_responses[2]]
    result = backend.list(target, details=True, new=True)
    assert isinstance(result, Iterable)
    assert sorted(result, key=itemgetter("archiveId")) == expected

    # Add archive_2 to history
    backend.history.append(
        {
            "backend": "ldp",
            "action": "read",
            "id": "archive_2",
            "filename": "2020-06-18.gz",
            "size": 23424233,
            "timestamp": "2020-10-07T16:37:25.887664+00:00",
        }
    )

    # We expect one request to retrieve details for archive 3.
    get_details_response = (response for response in details_responses[2:])

    # Given a history containing two matching archives and `new` and `details` set to
    # `True`, the `list` method should yield all archives with additional details,
    # except the matching ones.
    expected = [details_responses[2]]
    result = backend.list(target, details=True, new=True)
    assert isinstance(result, Iterable)
    assert sorted(result, key=itemgetter("archiveId")) == expected

    # Add archive_3 to history
    backend.history.append(
        {
            "backend": "ldp",
            "action": "read",
            "id": "archive_3",
            "filename": "2020-06-19.gz",
            "size": 23424233,
            "timestamp": "2020-10-07T16:37:25.887664+00:00",
        }
    )

    # Given a history containing all matching archives and `new` and `details` set to
    # `True`, the `list` method should yield nothing.
    expected = []
    result = backend.list(target, details=True, new=True)
    assert isinstance(result, Iterable)
    assert list(result) == expected


def test_backends_data_ldp_read_without_raw_ouput(ldp_backend, caplog):
    """Test the `LDPDataBackend.read method, given `raw_output` set to `False`, should
    log an error message and raise a `BackendParameterException`.
    """
    backend = ldp_backend()
    msg = (
        "Invalid `raw_output` value. LDP data backend doesn't support yielding "
        "dictionaries with `raw_output=False`"
    )
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendParameterException, match=msg):
            list(backend.read(query="archiveID", raw_output=False))

    assert ("ralph.backends.data.ldp", logging.ERROR, msg) in caplog.record_tuples


def test_backends_data_ldp_read_without_ignore_errors(ldp_backend, caplog, monkeypatch):
    """Test the `LDPDataBackend.read` method, given `ignore_errors` set to `False`,
    should log a warning message.
    """

    def mock_get(url):
        """Mock the OVH client get request."""

        return {"filename": "archive_name", "size": 10}

    backend = ldp_backend()

    backend = ldp_backend()
    monkeypatch.setattr(backend, "_url", lambda *_: "http://example.com")
    monkeypatch.setattr(backend.client, "get", mock_get)

    with caplog.at_level(logging.WARNING):
        with requests_mock.Mocker() as request_mocker:
            request_mocker.get("http://example.com")
            assert not list(backend.read(query="archiveID", ignore_errors=False))

    assert (
        "ralph.backends.data.ldp",
        logging.WARNING,
        "The `ignore_errors` argument is ignored",
    ) in caplog.record_tuples


def test_backends_data_ldp_read_with_invalid_query(ldp_backend):
    """Test the `LDPDataBackend.read` method given an invalid `query` argument should
    raise a `BackendParameterException`.
    """
    backend = ldp_backend()
    # Given no `query`, the `read` method should raise a `BackendParameterException`.
    error = "Invalid query. The query should be a valid archive name"
    with pytest.raises(BackendParameterException, match=error):
        list(backend.read())


def test_backends_data_ldp_read_with_failure(ldp_backend, monkeypatch):
    """Test the `LDPDataBackend.read` method, given a request failure, should raise a
    `BackendException`.
    """

    def mock_ovh_post_failure(url):
        """Mock the OVH Client post request always raising an exception."""
        raise ovh.exceptions.HTTPError("OVH Error")

    def mock_ovh_post(url):
        """Mock the OVH Client post request."""

        return {
            "expirationDate": "2020-10-13T12:59:37.326131+00:00",
            "url": (
                "https://storage.gra.cloud.ovh.net/v1/"
                "AUTH_-c3b123f595c46e789acdd1227eefc13/"
                "gra2-pcs/5eba98fb4fcb481001180e4b/"
                "2020-06-01.gz?"
                "temp_url_sig=e1b3ab10a9149a4ff5dcb95f40f21063780d26f7&"
                "temp_url_expires=1602593977"
            ),
        }

    class MockUnsuccessfulResponse:
        """Mock the requests response."""

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def raise_for_status(self):
            """Raise an `HttpError`."""

            raise requests.HTTPError("Failure during request")

    def mock_requests_get(url, stream=True, timeout=None):
        """Mock the request get method."""

        return MockUnsuccessfulResponse()

    # Freeze the ralph.utils.now() value.
    frozen_now = now()
    monkeypatch.setattr("ralph.backends.data.ldp.now", lambda: frozen_now)

    backend = ldp_backend()
    monkeypatch.setattr(backend.client, "post", mock_ovh_post)
    monkeypatch.setattr(requests, "get", mock_requests_get)

    error = r"Failed to read archive foo: Failure during request"
    with pytest.raises(BackendException, match=error):
        next(backend.read(query="foo"))

    monkeypatch.setattr(backend.client, "post", mock_ovh_post_failure)
    error = r"Failed to get 'foo' archive URL: OVH Error"
    with pytest.raises(BackendException, match=error):
        next(backend.read(query="foo"))


def test_backends_data_ldp_read_with_query(ldp_backend, monkeypatch, fs):
    """Test the `LDPDataBackend.read` method, given a query argument."""

    # Create fake archive to stream.
    archive_content = {"foo": "bar"}
    archive = gzip.compress(bytes(json.dumps(archive_content), encoding="utf-8"))

    def mock_ovh_post(url):
        """Mock the OVH Client post request."""

        return {
            "expirationDate": "2020-10-13T12:59:37.326131+00:00",
            "url": (
                "https://storage.gra.cloud.ovh.net/v1/"
                "AUTH_-c3b123f595c46e789acdd1227eefc13/"
                "gra2-pcs/5eba98fb4fcb481001180e4b/"
                "2020-06-01.gz?"
                "temp_url_sig=e1b3ab10a9149a4ff5dcb95f40f21063780d26f7&"
                "temp_url_expires=1602593977"
            ),
        }

    def mock_ovh_get(url):
        """Mock the OVH client get request."""

        return {
            "archiveId": "5d5c4c93-04a4-42c5-9860-f51fa4044aa1",
            "createdAt": "2020-06-18T04:38:59.436634+02:00",
            "filename": "2020-06-16.gz",
            "md5": "01585b394be0495e38dbb60b20cb40a9",
            "retrievalDelay": 0,
            "retrievalState": "sealed",
            "sha256": "645d8e21e6fdb8aa7ffc5c[...]9ce612d06df8dcf67cb29a45ca",
            "size": 67906662,
        }

    # Freeze the ralph.utils.now() value.
    frozen_now = now()
    monkeypatch.setattr("ralph.backends.data.ldp.now", lambda: frozen_now)

    backend = ldp_backend()
    monkeypatch.setattr(backend.client, "post", mock_ovh_post)
    monkeypatch.setattr(backend.client, "get", mock_ovh_get)
    monkeypatch.setattr(backend, "_url", lambda *_: "http://example.com")

    fs.create_dir(settings.APP_DIR)
    assert not os.path.exists(settings.HISTORY_FILE)

    with requests_mock.Mocker() as request_mocker:
        request_mocker.get("http://example.com", content=archive)
        result = b"".join(backend.read(query="5d5c4c93-04a4-42c5-9860-f51fa4044aa1"))

    assert os.path.exists(settings.HISTORY_FILE)
    assert backend.history == [
        {
            "backend": "ldp",
            "command": "read",
            "id": "bar/5d5c4c93-04a4-42c5-9860-f51fa4044aa1",
            "filename": "2020-06-16.gz",
            "size": 67906662,
            "timestamp": frozen_now,
        }
    ]

    assert json.loads(gzip_decode(result)) == archive_content


@pytest.mark.parametrize(
    "args,expected",
    [
        ([], "/dbaas/logs/foo/output/graylog/stream/bar/archive"),
        (["baz"], "/dbaas/logs/foo/output/graylog/stream/baz/archive"),
    ],
)
def test_backends_data_ldp_get_archive_endpoint_with_valid_input(
    ldp_backend, args, expected
):
    """Test the `LDPDataBackend.get_archive_endpoint` method, given valid input, should
    return the expected url.
    """

    assert ldp_backend()._get_archive_endpoint(*args) == expected


@pytest.mark.parametrize(
    "service_name,stream_id", [(None, "bar"), ("foo", None), (None, None)]
)
def test_backends_data_ldp_get_archive_endpoint_with_invalid_input(
    ldp_backend, service_name, stream_id
):
    """Test the `LDPDataBackend.get_archive_endpoint` method, given invalid input
    parameters, should raise a BackendParameterException.
    """

    with pytest.raises(
        BackendParameterException,
        match="LDPDataBackend requires to set both service_name and stream_id",
    ):
        ldp_backend(
            service_name=service_name, stream_id=stream_id
        )._get_archive_endpoint()

    with pytest.raises(
        BackendParameterException,
        match="LDPDataBackend requires to set both service_name and stream_id",
    ):
        ldp_backend(service_name=service_name, stream_id=None)._get_archive_endpoint(
            stream_id
        )


def test_backends_data_ldp_url(monkeypatch, ldp_backend):
    """Test the `LDPDataBackend.url` method."""

    archive_name = "5d49d1b3-a3eb-498c-9039-6a482166f888"
    archive_url = (
        "https://storage.gra.cloud.ovh.net/v1/"
        "AUTH_-c3b123f595c46e789acdd1227eefc13/"
        "gra2-pcs/5eba98fb4fcb481001180e4b/"
        "2020-06-01.gz?"
        "temp_url_sig=e1b3ab10a9149a4ff5dcb95f40f21063780d26f7&"
        "temp_url_expires=1602593977"
    )

    def mock_post(url):
        """Mock the OVH Client post request."""
        assert url.endswith(f"{archive_name}/url")
        return {"expirationDate": "2020-10-13T12:59:37.326131", "url": archive_url}

    backend = ldp_backend()
    monkeypatch.setattr(backend.client, "post", mock_post)
    assert backend._url(archive_name) == archive_url


def test_backends_data_ldp_close(ldp_backend, caplog):
    """Test that the `LDPDataBackend.close` method produces an info level log."""

    backend = ldp_backend()

    with caplog.at_level(logging.INFO):
        backend.close()

    assert (
        "ralph.backends.data.ldp",
        logging.INFO,
        "No open connections to close; skipping",
    ) in caplog.record_tuples
