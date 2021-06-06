"""Tests for the validate command using static fixtures"""

import json
import os

import pytest
from click.testing import CliRunner

from ralph.cli import cli
from ralph.exceptions import BadFormatException


def read_static_events(directory_path):
    """Yields tuples (file, comment, event) for events found at the directory path."""

    file_names = os.listdir(directory_path)
    for file_name in file_names:
        full_file_name = f"{directory_path}/{file_name}"
        with open(full_file_name, "r") as file:
            raw_static_events = file.read()
        try:
            parsed_static_events = json.loads(raw_static_events)
        except (TypeError, json.JSONDecodeError) as err:
            raise BadFormatException(
                f"File `{full_file_name}` contains invalid JSON"
            ) from err
        for event in parsed_static_events:
            comment = event.get("__comment__")
            del event["__comment__"]
            yield (file_name.replace(".json", ""), comment, event)


@pytest.mark.parametrize("_,__,event", read_static_events("./tests/models/data/edx"))
def test_static_edx_events(_, __, event):
    """Tests the validate command using the static events from the data directory."""

    event_str = json.dumps(event)
    runner = CliRunner()
    cli_args = ["-v", "DEBUG", "validate", "-f", "edx", "--fail-on-unknown"]
    result = runner.invoke(cli, cli_args, input=event_str)
    assert result.exception is None
    assert result.exit_code == 0
