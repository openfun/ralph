"""Tests for Ralph ldp storage backend"""

import datetime
import gzip
import json
import os.path
import sys
import uuid
from collections.abc import Iterable
from io import BytesIO
from pathlib import Path, PurePath
from urllib.parse import urlparse

import ovh
import pytest
import requests

from ralph.backends.storage.ldp import LDPStorage
from ralph.defaults import APP_DIR, HISTORY_FILE
from ralph.exceptions import BackendParameterException


def test_ldp_storage_instanciation():
    """Test the LDPStorage backend instanciation"""
    # pylint: disable=protected-access

    assert LDPStorage.name == "ldp"

    storage = LDPStorage(
        endpoint="ovh-eu",
        application_key="fake_key",
        application_secret="fake_secret",
        consumer_key="another_fake_key",
    )

    assert storage._endpoint == "ovh-eu"
    assert storage._application_key == "fake_key"
    assert storage._application_secret == "fake_secret"
    assert storage._consumer_key == "another_fake_key"
    assert storage.service_name is None
    assert storage.stream_id is None
    assert isinstance(storage.client, ovh.Client)


def test_archive_endpoint_property():
    """Test the LDPStorage _archive_endpoint property"""
    # pylint: disable=protected-access, pointless-statement

    storage = LDPStorage(
        endpoint="ovh-eu",
        application_key="fake_key",
        application_secret="fake_secret",
        consumer_key="another_fake_key",
        service_name="foo",
        stream_id="bar",
    )
    assert (
        storage._archive_endpoint == "/dbaas/logs/foo/output/graylog/stream/bar/archive"
    )

    storage.service_name = None
    with pytest.raises(
        BackendParameterException,
        match="LDPStorage backend instance requires to set both service_name and stream_id",
    ):
        storage._archive_endpoint

    storage.service_name = "foo"
    storage.stream_id = None
    with pytest.raises(
        BackendParameterException,
        match="LDPStorage backend instance requires to set both service_name and stream_id",
    ):
        storage._archive_endpoint

    storage.service_name = None
    with pytest.raises(
        BackendParameterException,
        match="LDPStorage backend instance requires to set both service_name and stream_id",
    ):
        storage._archive_endpoint


def test_details_method(monkeypatch):
    """Test the LDPStorage _details method"""
    # pylint: disable=protected-access

    def mock_get(url):
        """Mock OVH client get request"""

        name = PurePath(urlparse(url).path).name
        return {
            "archiveId": str(uuid.UUID(name)),
            "createdAt": "2020-06-18T04:38:59.436634+02:00",
            "filename": "2020-06-16.gz",
            "md5": "01585b394be0495e38dbb60b20cb40a9",
            "retrievalDelay": 0,
            "retrievalState": "sealed",
            "sha256": "645d8e21e6fdb8aa7ffc507acf091ada39dbdc9ce612d06df8dcf67cb29a45ca",
            "size": 67906662,
        }

    storage = LDPStorage(
        endpoint="ovh-eu",
        application_key="fake_key",
        application_secret="fake_secret",
        consumer_key="another_fake_key",
        service_name="ldp_fake",
        stream_id="bbf2d9fb-b092-4003-958b-1262dc902a1c",
    )

    # Apply the monkeypatch for requests.get to mock_get
    monkeypatch.setattr(storage.client, "get", mock_get)

    details = storage._details("5d49d1b3a3eb498c90396a482166f888")
    assert details.get("archiveId") == "5d49d1b3-a3eb-498c-9039-6a482166f888"


def test_url_method(monkeypatch):
    """Test the LDPStorage url method"""

    def mock_post(url):
        """Mock OVH Client post request"""
        # pylint: disable=unused-argument
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

    storage = LDPStorage(
        endpoint="ovh-eu",
        application_key="fake_key",
        application_secret="fake_secret",
        consumer_key="another_fake_key",
        service_name="ldp_fake",
        stream_id="bbf2d9fb-b092-4003-958b-1262dc902a1c",
    )

    # Apply the monkeypatch for requests.post to mock_get
    monkeypatch.setattr(storage.client, "post", mock_post)

    assert storage.url("5d49d1b3-a3eb-498c-9039-6a482166f888") == (
        "https://storage.gra.cloud.ovh.net/v1/"
        "AUTH_-c3b123f595c46e789acdd1227eefc13/"
        "gra2-pcs/5eba98fb4fcb481001180e4b/"
        "2020-06-01.gz?"
        "temp_url_sig=e1b3ab10a9149a4ff5dcb95f40f21063780d26f7&"
        "temp_url_expires=1602593977"
    )


def test_list_method(monkeypatch):
    """Test the LDPStorage list method with a blank history"""

    def mock_list(url):
        """Mock OVH client list stream archives get request"""
        # pylint: disable=unused-argument
        return [
            "5d5c4c93-04a4-42c5-9860-f51fa4044aa1",
            "997db3eb-b9ca-485d-810f-b530a6cef7c6",
            "08075b54-8d24-42ea-a509-9f10b0e3b416",
            "75c865fd-b4eb-4b2b-9290-e8166a187d50",
            "72e82041-7245-4ef1-b876-01964c6a8c50",
        ]

    storage = LDPStorage(
        endpoint="ovh-eu",
        application_key="fake_key",
        application_secret="fake_secret",
        consumer_key="another_fake_key",
        service_name="ldp_fake",
        stream_id="bbf2d9fb-b092-4003-958b-1262dc902a1c",
    )

    # Apply the monkeypatch for requests.post to mock_get
    monkeypatch.setattr(storage.client, "get", mock_list)

    archives = storage.list(details=False, new=False)
    assert isinstance(archives, Iterable)
    assert list(archives) == [
        "5d5c4c93-04a4-42c5-9860-f51fa4044aa1",
        "997db3eb-b9ca-485d-810f-b530a6cef7c6",
        "08075b54-8d24-42ea-a509-9f10b0e3b416",
        "75c865fd-b4eb-4b2b-9290-e8166a187d50",
        "72e82041-7245-4ef1-b876-01964c6a8c50",
    ]


def test_list_method_history_management(monkeypatch, fs):
    """Test the LDPStorage list method with an history"""
    # pylint: disable=invalid-name

    def mock_list(url):
        """Mock OVH client list stream archives get request"""
        # pylint: disable=unused-argument
        return [
            "5d5c4c93-04a4-42c5-9860-f51fa4044aa1",
            "997db3eb-b9ca-485d-810f-b530a6cef7c6",
            "08075b54-8d24-42ea-a509-9f10b0e3b416",
            "75c865fd-b4eb-4b2b-9290-e8166a187d50",
            "72e82041-7245-4ef1-b876-01964c6a8c50",
        ]

    storage = LDPStorage(
        endpoint="ovh-eu",
        application_key="fake_key",
        application_secret="fake_secret",
        consumer_key="another_fake_key",
        service_name="ldp_fake",
        stream_id="bbf2d9fb-b092-4003-958b-1262dc902a1c",
    )

    # Apply the monkeypatch for requests.post to mock_get
    monkeypatch.setattr(storage.client, "get", mock_list)

    # Create a fetch history
    fs.create_file(
        HISTORY_FILE,
        contents=json.dumps(
            [
                {
                    "backend": "ldp",
                    "command": "fetch",
                    "id": "5d5c4c93-04a4-42c5-9860-f51fa4044aa1",
                    "filename": "20201002.tgz",
                    "size": 23424233,
                    "fetched_at": "2020-10-07T16:37:25.887664+00:00",
                },
                {
                    "backend": "ldp",
                    "command": "fetch",
                    "id": "997db3eb-b9ca-485d-810f-b530a6cef7c6",
                    "filename": "20201002.tgz",
                    "size": 23424233,
                    "fetched_at": "2020-10-07T16:40:25.887664+00:00",
                },
                {
                    "backend": "ldp",
                    "command": "fetch",
                    "id": "08075b54-8d24-42ea-a509-9f10b0e3b416",
                    "filename": "20201002.tgz",
                    "size": 23424233,
                    "fetched_at": "2020-10-07T19:37:25.887664+00:00",
                },
            ]
        ),
    )

    archives = storage.list(details=False, new=True)
    assert isinstance(archives, Iterable)
    assert sorted(list(archives)) == sorted(
        [
            "75c865fd-b4eb-4b2b-9290-e8166a187d50",
            "72e82041-7245-4ef1-b876-01964c6a8c50",
        ]
    )


def test_list_method_with_details(monkeypatch):
    """Test the LDPStorage list method with detailled output"""

    details_responses = [
        {
            "archiveId": "5d5c4c93-04a4-42c5-9860-f51fa4044aa1",
            "createdAt": "2020-06-18T04:38:59.436634+02:00",
            "filename": "2020-06-16.gz",
            "md5": "01585b394be0495e38dbb60b20cb40a9",
            "retrievalDelay": 0,
            "retrievalState": "sealed",
            "sha256": "645d8e21e6fdb8aa7ffc507acf091ada39dbdc9ce612d06df8dcf67cb29a45ca",
            "size": 67906662,
        },
        {
            "archiveId": "997db3eb-b9ca-485d-810f-b530a6cef7c6",
            "createdAt": "2020-06-18T04:38:59.436634+02:00",
            "filename": "2020-06-17.gz",
            "md5": "01585b394be0495e38dbb60b20cb40a9",
            "retrievalDelay": 0,
            "retrievalState": "sealed",
            "sha256": "645d8e21e6fdb8aa7ffc507acf091ada39dbdc9ce612d06df8dcf67cb29a45ca",
            "size": 67906662,
        },
    ]
    get_details_response = (response for response in details_responses)

    def mock_get(url):
        """Mock OVH client get requests"""

        # list request
        if url.endswith("archive"):
            return [
                "5d5c4c93-04a4-42c5-9860-f51fa4044aa1",
                "997db3eb-b9ca-485d-810f-b530a6cef7c6",
            ]
        # details request
        return next(get_details_response)

    storage = LDPStorage(
        endpoint="ovh-eu",
        application_key="fake_key",
        application_secret="fake_secret",
        consumer_key="another_fake_key",
        service_name="ldp_fake",
        stream_id="bbf2d9fb-b092-4003-958b-1262dc902a1c",
    )

    # Apply the monkeypatch for requests.post to mock_get
    monkeypatch.setattr(storage.client, "get", mock_get)

    archives = storage.list(details=True, new=False)
    assert isinstance(archives, Iterable)
    assert list(archives) == details_responses


def test_read_method(monkeypatch, fs):
    """Test the LDPStorage read method with detailled output"""
    # pylint: disable=invalid-name

    # Create fake archive to stream
    archive_path = Path("/tmp/2020-06-16.gz")
    archive_content = {"foo": "bar"}
    with gzip.open(archive_path, "wb") as archive_file:
        archive_file.write(bytes(json.dumps(archive_content), encoding="utf-8"))

    def mock_ovh_post(url):
        """Mock OVH Client post request"""
        # pylint: disable=unused-argument

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
        """Mock OVH client get requests"""
        # pylint: disable=unused-argument

        return {
            "archiveId": "5d5c4c93-04a4-42c5-9860-f51fa4044aa1",
            "createdAt": "2020-06-18T04:38:59.436634+02:00",
            "filename": "2020-06-16.gz",
            "md5": "01585b394be0495e38dbb60b20cb40a9",
            "retrievalDelay": 0,
            "retrievalState": "sealed",
            "sha256": "645d8e21e6fdb8aa7ffc507acf091ada39dbdc9ce612d06df8dcf67cb29a45ca",
            "size": 67906662,
        }

    class MockRequestsResponse:
        """A basic mock for a requests response"""

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def iter_content(self, chunk_size):
            """Fake content file iteration"""
            # pylint: disable=no-self-use

            with archive_path.open("rb") as archive:
                while chunk := archive.read(chunk_size):
                    yield chunk

        def raise_for_status(self):
            """Do nothing for now"""

    def mock_requests_get(url, stream=True):
        """Mock requests get requests"""
        # pylint: disable=unused-argument

        return MockRequestsResponse()

    # Freeze the datetime.datetime.now() value
    freezed_now = datetime.datetime.now(tz=datetime.timezone.utc)

    class MockDatetime:
        """A mock class for a fixed datetime.now() value"""

        @classmethod
        def now(cls, **kwargs):
            """Always return the same testable now value"""
            # pylint: disable=unused-argument

            return freezed_now

    # Mock stdout stream
    class MockStdout:
        """A simple mock for sys.stdout.buffer"""

        buffer = BytesIO()

    mock_stdout = MockStdout()

    storage = LDPStorage(
        endpoint="ovh-eu",
        application_key="fake_key",
        application_secret="fake_secret",
        consumer_key="another_fake_key",
        service_name="ldp_fake",
        stream_id="bbf2d9fb-b092-4003-958b-1262dc902a1c",
    )

    # Apply monkeypatches
    monkeypatch.setattr(storage.client, "post", mock_ovh_post)
    monkeypatch.setattr(storage.client, "get", mock_ovh_get)
    monkeypatch.setattr(requests, "get", mock_requests_get)
    monkeypatch.setattr(datetime, "datetime", MockDatetime)
    monkeypatch.setattr(sys, "stdout", mock_stdout)

    fs.create_dir(str(APP_DIR))
    assert not os.path.exists(str(HISTORY_FILE))

    storage.read(name="5d5c4c93-04a4-42c5-9860-f51fa4044aa1")

    assert os.path.exists(str(HISTORY_FILE))
    assert storage.history == [
        {
            "backend": "ldp",
            "command": "fetch",
            "id": "5d5c4c93-04a4-42c5-9860-f51fa4044aa1",
            "filename": "2020-06-16.gz",
            "size": 67906662,
            "fetched_at": freezed_now.isoformat(),
        }
    ]

    mock_stdout.buffer.seek(0)
    with gzip.open(mock_stdout.buffer, "rb") as output:
        assert json.loads(output.read()) == archive_content


def test_write_method_with_details():
    """Test the LDPStorage write method"""

    storage = LDPStorage(
        endpoint="ovh-eu",
        application_key="fake_key",
        application_secret="fake_secret",
        consumer_key="another_fake_key",
        service_name="ldp_fake",
        stream_id="bbf2d9fb-b092-4003-958b-1262dc902a1c",
    )

    with pytest.raises(
        NotImplementedError,
        match="LDP storage backend is read-only, cannot write to fake",
    ):
        storage.write("fake", "content")
