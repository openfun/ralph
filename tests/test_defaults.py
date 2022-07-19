"""Tests for Ralph's configuration loading"""

from inspect import signature
from pathlib import Path

import pytest

from ralph.defaults import (
    APP_DIR,
    BACKENDS,
    CommaSeparatedTuple,
    get_settings,
    load_config,
)
from ralph.exceptions import ConfigurationException
from ralph.utils import import_string


# pylint: disable=invalid-name, unused-argument
def test_defaults_load_config_no_config(fs, monkeypatch):
    """Tests that loading when no configuration file is available results in load_config
    returning None.
    """

    config_path = APP_DIR / "config.yml"

    assert load_config(config_path) is None


# pylint: disable=invalid-name, unused-argument
def test_defaults_load_config_correct_config(fs, monkeypatch):
    """Tests that loading a correct configuration file works as intended."""

    config_path = APP_DIR / "config.yml"

    fs.create_file(config_path, contents="DEFAULT_BACKEND_CHUNK_SIZE: 5678")

    assert load_config(config_path)["DEFAULT_BACKEND_CHUNK_SIZE"] == 5678


# pylint: disable=invalid-name, unused-argument
def test_defaults_load_config_incorrect_config(fs, monkeypatch):
    """Tests that loading an incorrect configuration file raises a configuration
    exception."""

    config_path = APP_DIR / "config.yml"

    fs.create_file(config_path, contents="A: B: C")

    with pytest.raises(ConfigurationException):
        load_config(config_path)


def test_defaults_get_settings_field_value_priority(fs, monkeypatch):
    """Tests that the Settings object field values are defined in the following
    decending order of priority:

        1. Arguments passed to the initializer.
        2. Environment variables.
        3. Configuration file variables.
        4. Default field values.
    """

    # 4. Using default value.
    assert get_settings().AUTH_FILE == APP_DIR / "auth.json"

    # 3. Using configuration file value (overrides default value).
    config_path = APP_DIR / "config.yml"
    fs.create_file(config_path, contents="AUTH_FILE: /foo/bar/config")
    get_settings.cache_clear()
    assert get_settings().AUTH_FILE == Path("/foo/bar/config")

    # 2. Using environment variable value (overrides configuration value).
    monkeypatch.setenv("RALPH_AUTH_FILE", "/foo/bar/environment")
    get_settings.cache_clear()
    assert get_settings().AUTH_FILE == Path("/foo/bar/environment")

    # 1. Using argument value (overrides environment value).
    get_settings.cache_clear()
    assert get_settings(AUTH_FILE="/foo/bar/arg").AUTH_FILE == Path("/foo/bar/arg")


@pytest.mark.parametrize(
    "value,expected",
    [("foo", ("foo",)), (("foo",), ("foo",)), ("foo,bar,baz", ("foo", "bar", "baz"))],
)
def test_defaults_comma_separated_list_with_valid_values(value, expected):
    """Tests the CommaSeparatedTuple pydantic data type with valid values."""

    assert next(CommaSeparatedTuple.__get_validators__())(value) == expected
    assert get_settings(ES_HOSTS=value).ES_HOSTS == expected


def test_defaults_settings_should_define_all_backends_options():
    """Tests that Settings model defines all backends options."""

    settings_fields = get_settings().__fields__
    for backend_class_path in BACKENDS.values():
        backend_class = import_string(backend_class_path)
        for parameter in signature(backend_class.__init__).parameters.values():
            if parameter.name == "self":
                continue
            option = f"{backend_class.name}_{parameter.name}".upper()
            assert option in settings_fields
