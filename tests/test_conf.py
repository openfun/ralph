"""Tests for Ralph's configuration loading."""

from importlib import reload

import pytest
from pydantic import ValidationError

from ralph import conf
from ralph.backends.data.es import ESDataBackend
from ralph.conf import (
    AuthBackend,
    AuthBackends,
    CommaSeparatedTuple,
    Settings,
    parse_obj_as,
    settings,
)
from ralph.exceptions import ConfigurationException


def test_conf_settings_field_value_priority(fs, monkeypatch):
    """Test that the Settings object field values are defined in the following
    descending order of priority:

        1. Arguments passed to the initializer.
        2. Environment variables.
        3. Dotenv variables (.env)
        4. Default values.
    """

    # 4. Using default value.
    assert str(Settings().AUTH_FILE) == str(settings.APP_DIR / "auth.json")

    # 3. Using dotenv variables (overrides default value).
    fs.create_file(".env", contents="RALPH_AUTH_FILE=/dotenv\n")
    assert str(Settings().AUTH_FILE) == "/dotenv"

    # 2. Using environment variable value (overrides dotenv value).
    monkeypatch.setenv("RALPH_AUTH_FILE", "/environment")
    assert str(Settings().AUTH_FILE) == "/environment"

    # 1. Using argument value (overrides environment value).
    assert str(Settings(AUTH_FILE="/argument").AUTH_FILE) == "/argument"


@pytest.mark.parametrize(
    "value,expected",
    [
        ("foo", ("foo",)),
        (("foo",), ("foo",)),
        (["foo"], ("foo",)),
        ("foo,bar,baz", ("foo", "bar", "baz")),
    ],
)
def test_conf_comma_separated_list_with_valid_values(value, expected, monkeypatch):
    """Test the CommaSeparatedTuple pydantic data type with valid values."""
    assert parse_obj_as(CommaSeparatedTuple, value) == expected
    monkeypatch.setenv("RALPH_BACKENDS__DATA__ES__HOSTS", "".join(value))
    assert ESDataBackend().settings.HOSTS == expected


@pytest.mark.parametrize("value", [{}, None])
def test_conf_comma_separated_list_with_invalid_values(value):
    """Test the CommaSeparatedTuple pydantic data type with invalid values."""
    with pytest.raises(ValidationError, match="2 validation errors for function-after"):
        parse_obj_as(CommaSeparatedTuple, value)


@pytest.mark.parametrize(
    "value,is_valid,expected",
    [
        ("oidc", True, (AuthBackend.OIDC,)),
        ("basic", True, (AuthBackend.BASIC,)),
        ("bASIc", True, (AuthBackend.BASIC,)),
        ("oidc,basic", True, (AuthBackend.OIDC, AuthBackend.BASIC)),
        ("notvalid", False, None),
        ("basic,notvalid", False, None),
    ],
)
def test_conf_auth_backend(value, is_valid, expected, monkeypatch):
    """Test the AuthBackends data type with valid and invalid values."""
    if is_valid:
        assert parse_obj_as(AuthBackends, value) == expected
        monkeypatch.setenv("RALPH_RUNSERVER_AUTH_BACKENDS", "".join(value))
        reload(conf)
        assert conf.settings.RUNSERVER_AUTH_BACKENDS == expected
    else:
        with pytest.raises(ValueError, match="'notvalid' is not a valid AuthBackend"):
            parse_obj_as(AuthBackends, value)


def test_conf_core_settings_should_impact_settings_defaults(monkeypatch):
    """Test that core settings update application settings values."""
    monkeypatch.setenv("RALPH_APP_DIR", "/foo")
    monkeypatch.setenv("RALPH_LOCALE_ENCODING", "ascii")
    reload(conf)

    # Configuration.
    assert conf.Settings.model_config["env_file_encoding"] == "ascii"

    # Properties.
    assert str(conf.settings.APP_DIR) == "/foo"
    assert conf.settings.LOCALE_ENCODING == "ascii"

    # Defaults.
    assert str(conf.settings.AUTH_FILE) == "/foo/auth.json"


def test_conf_forbidden_scopes_without_authority(monkeypatch):
    """Test that using RESTRICT_BY_SCOPES without RESTRICT_BY_AUTHORITY raises an
    error."""

    monkeypatch.setenv("RALPH_LRS_RESTRICT_BY_AUTHORITY", False)
    monkeypatch.setenv("RALPH_LRS_RESTRICT_BY_SCOPES", True)

    with pytest.raises(
        ConfigurationException,
        match=(
            "LRS_RESTRICT_BY_AUTHORITY must be set to True if using "
            "LRS_RESTRICT_BY_SCOPES=True"
        ),
    ):
        reload(conf)
