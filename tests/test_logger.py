"""Tests for the ralph.logger module."""

import pytest
from click.testing import CliRunner

import ralph.logger
from ralph.cli import cli
from ralph.exceptions import ConfigurationException


# pylint: disable=invalid-name, unused-argument
def test_logger_exists(fs, monkeypatch):
    """Test the logging system when a correct configuration is provided."""
    mock_default_config = {
        "version": 1,
        "propagate": True,
        "formatters": {
            "ralph_format": {
                "format": "%(asctime)-23s %(levelname)-8s %(name)-8s %(message)s"
            },
        },
        "handlers": {
            "ralph_stderr": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "stream": "ext://sys.stderr",
                "formatter": "ralph_format",
            },
        },
        "loggers": {
            "ralph": {
                "handlers": ["ralph_stderr"],
                "level": "DEBUG",
            },
        },
    }

    fs.create_dir("/dev")
    fs.create_dir("foo")

    monkeypatch.setattr(ralph.logger.settings, "LOGGING", mock_default_config)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["write", "-b", "fs", "-t", "test_file", "--fs-default-directory-path", "foo"],
        input="test input",
    )

    assert result.exit_code == 0
    assert "Writing to target test_file for the configured fs backend" in result.output
    assert "Backend parameters:" in result.output


# pylint: disable=invalid-name, unused-argument
def test_logger_no_config(fs, monkeypatch):
    """Test that an error occurs when no logging configuration exists."""
    mock_default_config = None

    monkeypatch.setattr(ralph.logger.settings, "LOGGING", mock_default_config)

    runner = CliRunner()

    with pytest.raises(ConfigurationException):
        result = runner.invoke(cli, ["list", "-b", "fs"], catch_exceptions=False)
        assert result.exit_code == 1


# pylint: disable=invalid-name, unused-argument
def test_logger_bad_config(fs, monkeypatch):
    """Test that an error occurs when a logging is improperly configured."""
    mock_default_config = "this is not a valid json"

    monkeypatch.setattr(ralph.logger.settings, "LOGGING", mock_default_config)

    runner = CliRunner()

    with pytest.raises(ConfigurationException):
        result = runner.invoke(cli, ["list", "-b", "fs"], catch_exceptions=False)
        assert result.exit_code == 1
