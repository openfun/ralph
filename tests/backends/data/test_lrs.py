"""Tests for Ralph Async LRS HTTP backend."""

import pytest
from pydantic import AnyHttpUrl, parse_obj_as

from ralph.backends.data.lrs import LRSDataBackend, LRSDataBackendSettings, LRSHeaders
from ralph.backends.lrs.base import LRSStatementsQuery


@pytest.mark.anyio
def test_backends_http_lrs_default_instantiation(monkeypatch, fs):
    """Test the `LRSDataBackend` default instantiation."""
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
        monkeypatch.delenv(f"RALPH_BACKENDS__DATA__LRS__{name}", raising=False)

    assert LRSDataBackend.name == "lrs"
    assert LRSDataBackend.settings_class == LRSDataBackendSettings
    backend = LRSDataBackend()
    assert backend.query_class == LRSStatementsQuery
    assert backend.base_url == parse_obj_as(AnyHttpUrl, "http://0.0.0.0:8100")
    assert backend.auth == ("ralph", "secret")
    assert backend.settings.HEADERS == LRSHeaders()
    assert backend.settings.STATUS_ENDPOINT == "/__heartbeat__"
    assert backend.settings.STATEMENTS_ENDPOINT == "/xAPI/statements"

    # Test overriding default values with environment variables.
    monkeypatch.setenv("RALPH_BACKENDS__DATA__LRS__USERNAME", "foo")
    backend = LRSDataBackend()
    assert backend.auth == ("foo", "secret")


def test_backends_http_lrs_instantiation_with_settings():
    """Test the LRS backend default instantiation."""

    headers = LRSHeaders(
        X_EXPERIENCE_API_VERSION="1.0.3", CONTENT_TYPE="application/json"
    )
    settings = LRSDataBackendSettings(
        BASE_URL="http://fake-lrs.com",
        USERNAME="user",
        PASSWORD="pass",
        HEADERS=headers,
        STATUS_ENDPOINT="/fake-status-endpoint",
        STATEMENTS_ENDPOINT="/xAPI/statements",
    )

    assert LRSDataBackend.name == "lrs"
    assert LRSDataBackend.settings_class == LRSDataBackendSettings
    backend = LRSDataBackend(settings)
    assert backend.query_class == LRSStatementsQuery
    assert isinstance(backend.base_url, AnyHttpUrl)
    assert backend.auth == ("user", "pass")
    assert backend.settings.HEADERS.CONTENT_TYPE == "application/json"
    assert backend.settings.HEADERS.X_EXPERIENCE_API_VERSION == "1.0.3"
    assert backend.settings.STATUS_ENDPOINT == "/fake-status-endpoint"
    assert backend.settings.STATEMENTS_ENDPOINT == "/xAPI/statements"
