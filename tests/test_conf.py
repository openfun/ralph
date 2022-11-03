"""Tests for Ralph's configuration loading."""

from importlib import reload
from inspect import signature

import pytest

from ralph import conf
from ralph.conf import CommaSeparatedTuple, Settings, settings
from ralph.utils import import_string


def test_conf_settings_field_value_priority(fs, monkeypatch):
    """Tests that the Settings object field values are defined in the following
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
    [("foo", ("foo",)), (("foo",), ("foo",)), ("foo,bar,baz", ("foo", "bar", "baz"))],
)
def test_conf_comma_separated_list_with_valid_values(value, expected, monkeypatch):
    """Tests the CommaSeparatedTuple pydantic data type with valid values."""

    assert next(CommaSeparatedTuple.__get_validators__())(value) == expected
    monkeypatch.setenv("RALPH_BACKENDS__DATABASE__ES__HOSTS", "".join(value))
    assert Settings().BACKENDS.DATABASE.ES.HOSTS == expected


@pytest.mark.parametrize("value", [{}, [], None])
def test_conf_comma_separated_list_with_invalid_values(value):
    """Tests the CommaSeparatedTuple pydantic data type with invalid values."""

    with pytest.raises(TypeError, match="Invalid comma separated list"):
        next(CommaSeparatedTuple.__get_validators__())(value)


def test_conf_settings_should_define_all_backends_options():
    """Tests that Settings model defines all backends options."""

    for _, backends in settings.BACKENDS:
        for _, backend in backends:
            # pylint: disable=protected-access
            backend_class = import_string(backend._class_path)
            for parameter in signature(backend_class.__init__).parameters.values():
                if parameter.name == "self":
                    continue
                assert hasattr(backend, parameter.name.upper())


def test_conf_core_settings_should_impact_settings_defaults(monkeypatch):
    """Tests that core settings update application settings values."""

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
    assert conf.settings.BACKENDS.STORAGE.FS.PATH == "/foo/archives"
