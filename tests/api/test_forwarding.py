"""Tests for the xAPI statements forwarding background task."""

import json
import logging

import pytest
from httpx import RequestError
from pydantic import ValidationError

from ralph.api.forwarding import forward_xapi_statements, get_active_xapi_forwardings
from ralph.conf import Settings, XapiForwardingConfigurationSettings

# from tests.fixtures.hypothesis_strategies import custom_builds, custom_given
from tests.factories import mock_instance


def test_api_forwarding_with_valid_configuration(
    monkeypatch,
):
    """Test the settings, given a valid forwarding configuration, should not raise an
    exception.
    """
    forwarding_settings = mock_instance(XapiForwardingConfigurationSettings)

    monkeypatch.delenv("RALPH_XAPI_FORWARDINGS", raising=False)
    settings = Settings()

    assert settings.XAPI_FORWARDINGS == []

    monkeypatch.setenv("RALPH_XAPI_FORWARDINGS", f"[{forwarding_settings.json()}]")
    settings = Settings()
    assert len(settings.XAPI_FORWARDINGS) == 1
    assert settings.XAPI_FORWARDINGS[0] == forwarding_settings


@pytest.mark.parametrize(
    "missing_key",
    ["url", "is_active", "basic_username", "basic_password", "max_retries", "timeout"],
)
def test_api_forwarding_configuration_with_missing_field(missing_key):
    """Test the forwarding configuration, given a missing field, should raise a
    validation exception.
    """

    forwarding = mock_instance(XapiForwardingConfigurationSettings)

    forwarding_dict = json.loads(forwarding.json())
    del forwarding_dict[missing_key]
    with pytest.raises(ValidationError, match=f"{missing_key}\n  field required"):
        XapiForwardingConfigurationSettings(**forwarding_dict)


def test_api_forwarding_get_active_xapi_forwardings_with_empty_forwardings(
    monkeypatch, caplog
):
    """Test that the get_active_xapi_forwardings function, given an empty forwarding
    configuration, should log that forwarding is inactive and return an empty list.
    """
    expected_log = "No xAPI forwarding configured; forwarding is disabled."
    # RALPH_XAPI_FORWARDINGS not set
    monkeypatch.delenv("RALPH_XAPI_FORWARDINGS", raising=False)
    monkeypatch.setattr("ralph.api.forwarding.settings", Settings())
    get_active_xapi_forwardings.cache_clear()
    with caplog.at_level(logging.INFO):
        assert get_active_xapi_forwardings() == []

    assert caplog.record_tuples[0][2] == expected_log

    # RALPH_XAPI_FORWARDINGS set to empty list
    monkeypatch.setenv("RALPH_XAPI_FORWARDINGS", "[]")
    monkeypatch.setattr("ralph.api.forwarding.settings", Settings())
    get_active_xapi_forwardings.cache_clear()
    with caplog.at_level(logging.INFO):
        assert get_active_xapi_forwardings() == []

    assert caplog.record_tuples[0][2] == expected_log


def test_api_forwarding_get_active_xapi_forwardings_with_inactive_forwardings(
    monkeypatch, caplog
):
    """Test that the get_active_xapi_forwardings function, given a forwarding
    configuration containing inactive forwardings, should log which forwarding
    configurations are inactive and return a list containing only active forwardings.
    """

    active_forwarding = mock_instance(
        XapiForwardingConfigurationSettings, is_active=True
    )
    inactive_forwarding = mock_instance(
        XapiForwardingConfigurationSettings, is_active=False
    )

    active_forwarding_json = active_forwarding.json()
    inactive_forwarding_json = inactive_forwarding.json()

    # One inactive forwarding and no active forwarding.
    monkeypatch.setenv("RALPH_XAPI_FORWARDINGS", f"[{inactive_forwarding_json}]")
    monkeypatch.setattr("ralph.api.forwarding.settings", Settings())
    get_active_xapi_forwardings.cache_clear()
    caplog.clear()
    with caplog.at_level(logging.INFO):
        assert get_active_xapi_forwardings() == []

    msg = (
        f"The RALPH_XAPI_FORWARDINGS configuration value: '{inactive_forwarding}' is "
        "not active. It will be ignored."
    )
    assert len(caplog.record_tuples) == 1
    assert caplog.record_tuples[0][2] == msg

    # Two inactive forwardings and one active forwarding.
    forwardings = [
        inactive_forwarding_json,
        active_forwarding_json,
        inactive_forwarding_json,
    ]
    monkeypatch.setenv("RALPH_XAPI_FORWARDINGS", f"[{', '.join(forwardings)}]")
    monkeypatch.setattr("ralph.api.forwarding.settings", Settings())
    get_active_xapi_forwardings.cache_clear()
    caplog.clear()
    with caplog.at_level(logging.INFO):
        assert get_active_xapi_forwardings() == [active_forwarding]

    assert len(caplog.record_tuples) == 2
    assert caplog.record_tuples[0][2] == msg
    assert caplog.record_tuples[1][2] == msg


@pytest.mark.anyio
@pytest.mark.parametrize("statements", [[{}, {"id": 1}]])
async def test_api_forwarding_forward_xapi_statements_with_successful_request(
    monkeypatch, caplog, statements
):
    """Test the forward_xapi_statements function should log the forwarded statements
    count if the request was successful.
    """

    forwarding = mock_instance(
        XapiForwardingConfigurationSettings, max_retries=1, is_active=True
    )

    class MockSuccessfulResponse:
        """Dummy Successful Response."""

        @staticmethod
        def raise_for_status():
            """Does not raise any exceptions."""

    async def post_success(*args, **kwargs):
        """Return a MockSuccessfulResponse instance."""
        return MockSuccessfulResponse()

    monkeypatch.setattr("ralph.api.forwarding.AsyncClient.post", post_success)
    monkeypatch.setenv("RALPH_XAPI_FORWARDINGS", f"[{forwarding.json()}]")
    monkeypatch.setattr("ralph.api.forwarding.settings", Settings())
    get_active_xapi_forwardings.cache_clear()

    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        await forward_xapi_statements(statements, method="post")

    assert [
        f"Forwarded {len(statements)} statements to {forwarding.url} with success."
    ] == [
        message
        for source, _, message in caplog.record_tuples
        if source == "ralph.api.forwarding"
    ]


@pytest.mark.anyio
@pytest.mark.parametrize("statements", [[{}, {"id": 1}]])
async def test_api_forwarding_forward_xapi_statements_with_unsuccessful_request(
    monkeypatch, caplog, statements
):
    """Test the forward_xapi_statements function should log the error if the request
    was successful.
    """

    forwarding = mock_instance(
        XapiForwardingConfigurationSettings,
        max_retries=3,
        is_active=True,
    )

    class MockUnsuccessfulResponse:
        """Dummy Failing Response."""

        @staticmethod
        def raise_for_status():
            """Dummy raise_for_status method that is always raising an exception."""
            raise RequestError("Failure during request.")

    async def post_fail(*args, **kwargs):
        """Return a MockUnsuccessfulResponse instance."""
        return MockUnsuccessfulResponse()

    monkeypatch.setattr("ralph.api.forwarding.AsyncClient.post", post_fail)
    monkeypatch.setenv("RALPH_XAPI_FORWARDINGS", f"[{forwarding.json()}]")
    monkeypatch.setattr("ralph.api.forwarding.settings", Settings())
    get_active_xapi_forwardings.cache_clear()

    caplog.clear()
    with caplog.at_level(logging.ERROR):
        await forward_xapi_statements(statements, method="post")

    assert ["Failed to forward xAPI statements. Failure during request."] == [
        message
        for source, _, message in caplog.record_tuples
        if source == "ralph.api.forwarding"
    ]
