"""Tests for Ralph's configuration loading"""

from os import environ

import pytest

import ralph.defaults
from ralph.defaults import APP_DIR, config, load_config
from ralph.exceptions import ConfigurationException


# pylint: disable=invalid-name, unused-argument
def test_defaults_config_default(fs, monkeypatch):
    """Tests that when no value is given, the default parameter is chosen."""

    assert environ.get("RALPH_HISTORY_FILE", None) is None
    assert config("RALPH_HISTORY_FILE", "history_default") == "history_default"


# pylint: disable=invalid-name, unused-argument
def test_defaults_config_file(fs, monkeypatch):
    """Tests that when the environment and command-line arguments don't specify a
    value, the value from the config file is taken instead."""

    config_mock = {"RALPH_HISTORY_FILE": "history_config_file"}

    monkeypatch.setattr(ralph.defaults, "CONFIG", config_mock)

    assert environ.get("RALPH_HISTORY_FILE", None) is None
    assert config("RALPH_HISTORY_FILE", "history_default") == "history_config_file"


# pylint: disable=invalid-name, unused-argument
def test_defaults_config_env(fs, monkeypatch):
    """Tests that when the environment specifies a value, it is chosen instead of
    the configuration file's value."""

    config_mock = {"RALPH_HISTORY_FILE": "history_config_file"}

    monkeypatch.setattr(ralph.defaults, "CONFIG", config_mock)
    monkeypatch.setenv("RALPH_HISTORY_FILE", "history_env")

    assert config("RALPH_HISTORY_FILE", "history_default") == "history_env"


# pylint: disable=invalid-name, unused-argument
def test_defaults_load_config_no_config(fs, monkeypatch):
    """Tests that loading when no configuration file is available results in
    load_config returning None."""

    config_path = APP_DIR / "config.yml"

    assert load_config(config_path) is None


# pylint: disable=invalid-name, unused-argument
def test_defaults_load_config_correct_config(fs, monkeypatch):
    """Tests that loading a correct configuration file works as intended."""

    config_path = APP_DIR / "config.yml"

    fs.create_file(config_path, contents="DEFAULT_BACKEND_CHUNCK_SIZE: 5678")

    assert load_config(config_path)["DEFAULT_BACKEND_CHUNCK_SIZE"] == 5678


# pylint: disable=invalid-name, unused-argument
def test_defaults_load_config_incorrect_config(fs, monkeypatch):
    """Tests that loading an incorrect configuration file raises a configuration
    exception."""

    config_path = APP_DIR / "config.yml"

    fs.create_file(config_path, contents="A: B: C")

    with pytest.raises(ConfigurationException):
        load_config(config_path)
