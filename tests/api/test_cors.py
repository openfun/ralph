"""Tests for the health check endpoints."""

import importlib
import json
import logging

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ralph.conf import Settings

ALLOW_ORIGINS = [
    "https://my-allowed-origin.com",
    "https://my-other-allowed-origin.com",
    "https://yet.another.origin.com",
    "http://my-local-origin:8080",
]
ALLOW_ORIGINS_INVALID = [
    "htts://wrong-scheme.com",
    "https-wrong-format.com",
    "http:/another.wrong.format",
    "https://trailing-slash.com/",
]


def test_cors_allow_origin_valid_configuration(
    monkeypatch,
):
    """Test the settings, given a valid CORS AllowOrigin valid configuration,
    should not raise an exception.
    """
    monkeypatch.delenv("RALPH_RUNSERVER_CORS_ALLOW_ORIGINS", raising=False)
    settings = Settings()
    assert settings.RUNSERVER_CORS_ALLOW_ORIGINS == []

    monkeypatch.setenv("RALPH_RUNSERVER_CORS_ALLOW_ORIGINS", json.dumps(ALLOW_ORIGINS))
    settings = Settings()
    assert len(settings.RUNSERVER_CORS_ALLOW_ORIGINS) == len(ALLOW_ORIGINS)
    for i in range(len(settings.RUNSERVER_CORS_ALLOW_ORIGINS)):
        assert settings.RUNSERVER_CORS_ALLOW_ORIGINS[i] == ALLOW_ORIGINS[i]


def test_cors_allow_origin_invalid_configuration(
    monkeypatch,
):
    """Test the settings, given an invalid CORS AllowOrigin valid configuration,
    should raise an exception.
    """
    for invalid_origin in ALLOW_ORIGINS_INVALID:
        monkeypatch.delenv("RALPH_RUNSERVER_CORS_ALLOW_ORIGINS", raising=False)
        settings = Settings()
        assert settings.RUNSERVER_CORS_ALLOW_ORIGINS == []
        monkeypatch.setenv(
            "RALPH_RUNSERVER_CORS_ALLOW_ORIGINS", json.dumps([invalid_origin])
        )
        with pytest.raises(ValidationError):
            settings = Settings()
            logging.critical(settings.RUNSERVER_CORS_ALLOW_ORIGINS)


ORIGIN = "https://my-allowed-origin.com"


def _build_app(monkeypatch, origins: list):
    monkeypatch.setenv("RALPH_RUNSERVER_CORS_ALLOW_ORIGINS", json.dumps(origins))
    import ralph.conf

    importlib.reload(ralph.conf)
    import ralph.api

    importlib.reload(ralph.api)
    return ralph.api.app


@pytest.fixture(autouse=True)
def _restore():
    """Reload modules with the original environment after each test."""
    yield
    import ralph.api
    import ralph.conf

    importlib.reload(ralph.conf)
    importlib.reload(ralph.api)


def test_preflight_allowed_origin(monkeypatch):
    app = _build_app(monkeypatch, [ORIGIN])
    response = TestClient(app).options(
        "/xAPI/statements/",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization,X-Experience-API-Version",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert "authorization" in response.headers["access-control-allow-headers"].lower()


def test_preflight_disallowed_origin(monkeypatch):
    app = _build_app(monkeypatch, [ORIGIN])
    response = TestClient(app).options(
        "/xAPI/statements/",
        headers={"Origin": "https://evil.com", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in response.headers


def test_no_middleware_when_setting_empty(monkeypatch):
    app = _build_app(monkeypatch, [])
    response = TestClient(app).options(
        "/xAPI/statements/",
        headers={"Origin": ORIGIN, "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in response.headers
