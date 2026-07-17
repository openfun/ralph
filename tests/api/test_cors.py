"""Tests for the health check endpoints."""

import json
import logging

import pytest
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
    "http:/another.wrong.format" "https://trailing-slash.com/",
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
