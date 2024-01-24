"""Tests for Ralph flavors dependencies"""

import importlib
import re
import sys

import pytest
from click.testing import CliRunner

from ralph import cli


def test_dependencies_ralph_command_requires_click(monkeypatch):
    """Test Click module installation while executing the ralph command."""

    monkeypatch.setitem(sys.modules, "click", None)

    # Force ralph.cli reload now that click is considered as missing
    if "ralph.cli" in sys.modules:
        del sys.modules["ralph.cli"]

    with pytest.raises(
        ModuleNotFoundError,
        match=re.escape(
            "You need to install 'cli' optional dependencies to use the ralph "
            "command: pip install ralph-malph[cli]"
        ),
    ):
        importlib.import_module("ralph.cli")


def test_dependencies_runserver_subcommand_requires_uvicorn(monkeypatch):
    """Test Uvicorn module installation while executing the runserver sub command."""

    monkeypatch.delattr(cli, "uvicorn")
    monkeypatch.setattr(cli, "configure_logging", lambda: None)
    runner = CliRunner()
    result = runner.invoke(cli.cli, "runserver es".split())
    assert isinstance(result.exception, ModuleNotFoundError)
    assert str(result.exception) == (
        "You need to install 'lrs' optional dependencies to use the runserver "
        "command: pip install ralph-malph[lrs]"
    )
