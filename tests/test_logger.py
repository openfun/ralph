"""Tests for the ralph.logger module"""

import pytest
from click.testing import CliRunner

import ralph.logger
from ralph.cli import cli
from ralph.exceptions import ConfigurationException


# pylint: disable=invalid-name, unused-argument
def test_logger_exists(fs, monkeypatch):
    """Tests the logging system when a correct configuration is provided."""

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

    monkeypatch.setattr(ralph.logger, "LOGGING_CONFIG", mock_default_config)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["push", "-b", "fs", "test_file"],
        input="test input",
    )

    assert result.exit_code == 0
    assert "Pushing archive test_file to the configured fs backend" in result.output
    assert "Backend parameters:" in result.output


# pylint: disable=invalid-name, unused-argument
def test_logger_no_config(fs, monkeypatch):
    """Tests that an error occurs when no logging configuration exists."""

    mock_default_config = None

    monkeypatch.setattr(ralph.logger, "LOGGING_CONFIG", mock_default_config)

    runner = CliRunner()

    with pytest.raises(ConfigurationException):
        result = runner.invoke(cli, ["list", "-b", "fs"], catch_exceptions=False)
        assert result.exit_code == 1


# pylint: disable=invalid-name, unused-argument
def test_logger_bad_config(fs, monkeypatch):
    """Tests that an error occurs when a logging is improperly configured."""

    mock_default_config = "this is not a valid json"

    monkeypatch.setattr(ralph.logger, "LOGGING_CONFIG", mock_default_config)

    runner = CliRunner()

    with pytest.raises(ConfigurationException):
        result = runner.invoke(cli, ["list", "-b", "fs"], catch_exceptions=False)
        assert result.exit_code == 1
