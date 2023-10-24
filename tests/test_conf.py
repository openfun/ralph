"""Tests for Ralph's configuration loading."""

from importlib import reload

import pytest

from ralph import conf
from ralph.backends.conf import BackendSettings
from ralph.conf import CommaSeparatedTuple, Settings, settings
from ralph.exceptions import ConfigurationException


def test_conf_settings_field_value_priority(fs, monkeypatch):
    """Test that the Settings object field values are defined in the following
    descending order of priority:

        1. Arguments passed to the initializer.
        2. Environment variables.
        3. Dotenv variables (.env)
        4. Default values.
    """
    # pylint: disable=invalid-name

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
    assert next(CommaSeparatedTuple.__get_validators__())(value) == expected
    monkeypatch.setenv("RALPH_BACKENDS__DATA__ES__HOSTS", "".join(value))
    assert BackendSettings().BACKENDS.DATA.ES.HOSTS == expected


@pytest.mark.parametrize("value", [{}, None])
def test_conf_comma_separated_list_with_invalid_values(value):
    """Test the CommaSeparatedTuple pydantic data type with invalid values."""
    with pytest.raises(TypeError, match="Invalid comma separated list"):
        next(CommaSeparatedTuple.__get_validators__())(value)


def test_conf_core_settings_should_impact_settings_defaults(monkeypatch):
    """Test that core settings update application settings values."""
    monkeypatch.setenv("RALPH_APP_DIR", "/foo")
    monkeypatch.setenv("RALPH_LOCALE_ENCODING", "ascii")
    reload(conf)

    # Configuration.
    assert conf.Settings.Config.env_file_encoding == "ascii"

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
