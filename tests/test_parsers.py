"""Tests for ralph.parsers module."""

import gzip
import logging
import shutil
from io import StringIO

import pytest

from ralph.conf import settings
from ralph.parsers import GELFParser


# pylint: disable=invalid-name
def test_parsers_gelfparser_parse_empty_file():
    """Tests the GELFParser parsing with an empty file."""
    parser = GELFParser()

    empty_file = StringIO()
    with pytest.raises(StopIteration):
        next(parser.parse(empty_file))


def test_parsers_gelfparser_parse_raw_file(gelf_logger):
    """Tests the GELFParser parsing using a flat GELF file."""
    parser = GELFParser()

    # Create two log entries
    gelf_logger.info('{"username": "foo"}')
    gelf_logger.info('{"username": ""}')

    with open(
        gelf_logger.handlers[0].stream.name, encoding=settings.LOCALE_ENCODING
    ) as stream:
        events = list(parser.parse(stream))

    assert len(events) == 2
    assert events[0] == '{"username": "foo"}'
    assert events[1] == '{"username": ""}'


# pylint: disable=invalid-name,unused-argument
def test_parsers_gelfparser_parse_gzipped_file(fs, gelf_logger):
    """Tests the GELFParser parsing using a gzipped GELF file."""
    gelf_logger.info('{"username": "foo"}')
    gelf_logger.info('{"username": "bar"}')

    # Compress the log file
    log_file_name = gelf_logger.handlers[0].stream.name
    gzipped_log_file_name = f"{log_file_name}.gz"
    with open(log_file_name, "rb") as log_file:
        with gzip.open(gzipped_log_file_name, "wb") as gzipped_log_file:
            shutil.copyfileobj(log_file, gzipped_log_file)

    parser = GELFParser()
    with open(
        gelf_logger.handlers[0].stream.name, encoding=settings.LOCALE_ENCODING
    ) as stream:
        events = list(parser.parse(stream))

    assert len(events) == 2
    assert events[0] == '{"username": "foo"}'
    assert events[1] == '{"username": "bar"}'


def test_parsers_gelfparser_parse_partially_invalid_file(caplog):
    """Tests the GELFParser with a file containing invalid JSON strings."""
    with StringIO() as file:
        file.writelines(
            [
                # This is invalid gelf, but we assume it's valid in our case
                '{"short_message": "This seems valid."}\n',
                # Invalid json
                "{ This is not valid json and raises json.decoder.JSONDecodeError\n",
                # Valid json but invalid gelf raises KeyError:
                # key "short_message" not found
                "{}\n",
                # As above but raises TypeError:
                # list indices must be integers or slices, not str
                "[]\n",
                # Another assumed valid gelf
                '{"short_message": {"username": "This seems valid too."}}\n',
            ]
        )

        file.seek(0)
        parser = GELFParser()
        events = list(parser.parse(file))

    assert len(events) == 2
    assert events[0] == "This seems valid."
    assert events[1] == {"username": "This seems valid too."}

    caplog.clear()
    with StringIO() as file:
        file.write("{ This is not valid json and raises json.decoder.JSONDecodeError\n")
        file.seek(0)
        parser = GELFParser()
        with caplog.at_level(logging.DEBUG):
            events = list(parser.parse(file))

    assert len(events) == 0
    assert (
        "ralph.parsers",
        logging.ERROR,
        "Input event '{ This is not valid json and raises "
        "json.decoder.JSONDecodeError\n' "
        "is not a valid JSON string! It will be ignored.",
    ) in caplog.record_tuples
    assert (
        "ralph.parsers",
        logging.DEBUG,
        "Raised error was: Expecting property name enclosed in double quotes: "
        "line 1 column 3 (char 2)",
    ) in caplog.record_tuples

    caplog.clear()
    with StringIO() as file:
        file.write("{}")
        file.seek(0)
        parser = GELFParser()
        with caplog.at_level(logging.DEBUG):
            events = list(parser.parse(file))

    assert len(events) == 0
    assert (
        "ralph.parsers",
        logging.ERROR,
        "Input event '{}' doesn't comply with GELF format! It will be ignored.",
    ) in caplog.record_tuples
    assert (
        "ralph.parsers",
        logging.DEBUG,
        "Raised error was: 'short_message'",
    ) in caplog.record_tuples

    caplog.clear()
    with StringIO() as file:
        file.write("[]")
        file.seek(0)
        parser = GELFParser()
        with caplog.at_level(logging.DEBUG):
            events = list(parser.parse(file))

    assert len(events) == 0
    assert (
        "ralph.parsers",
        logging.ERROR,
        "Input event '[]' is not a valid JSON string! It will be ignored.",
    ) in caplog.record_tuples
    assert (
        "ralph.parsers",
        logging.DEBUG,
        "Raised error was: list indices must be integers or slices, not str",
    ) in caplog.record_tuples
