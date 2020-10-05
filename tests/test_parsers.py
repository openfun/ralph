"""
Tests for ralph.parsers module.
"""
import gzip
import shutil

import pytest

from ralph.parsers import GELFParser


def test_gelfparser_parse_non_existing_file():
    """Test the GELFParser with a file path that does not exist."""

    parser = GELFParser()

    # Input log file does not exists
    with pytest.raises(OSError):
        next(parser.parse("/i/do/not/exist"))


# pylint: disable=invalid-name
def test_gelfparser_parse_empty_file(fs):
    """Test the GELFParser parsing with an empty file."""

    parser = GELFParser()

    # Input log file is empty
    empty_file_path = "/var/log/empty"
    fs.create_file(empty_file_path)
    with pytest.raises(StopIteration):
        next(parser.parse(empty_file_path))


def test_gelfparser_parse_raw_file(gelf_logger):
    """Test the GELFParser parsing using a flat GELF file."""

    parser = GELFParser()

    # Create two log entries
    gelf_logger.info('{"username": "foo"}')
    gelf_logger.info('{"username": ""}')

    events = list(parser.parse(gelf_logger.handlers[0].stream.name))
    assert len(events) == 2
    assert events[0] == '{"username": "foo"}'
    assert events[1] == '{"username": ""}'


# pylint: disable=invalid-name,unused-argument
def test_gelfparser_parse_gzipped_file(fs, gelf_logger):
    """Test the GELFParser parsing using a gzipped GELF file."""

    gelf_logger.info('{"username": "foo"}')
    gelf_logger.info('{"username": "bar"}')

    # Compress the log file
    log_file_name = gelf_logger.handlers[0].stream.name
    gzipped_log_file_name = f"{log_file_name}.gz"
    with open(log_file_name, "rb") as log_file:
        with gzip.open(gzipped_log_file_name, "wb") as gzipped_log_file:
            shutil.copyfileobj(log_file, gzipped_log_file)

    parser = GELFParser()
    events = list(parser.parse(gelf_logger.handlers[0].stream.name))
    assert len(events) == 2
    assert events[0] == '{"username": "foo"}'
    assert events[1] == '{"username": "bar"}'


# pylint: disable=invalid-name,unused-argument
def test_gelfparser_parse_with_various_chunksizes(fs, gelf_logger):
    """Test the GELFParser parsing using different chunksizes."""

    gelf_logger.info('{"username": "foo"}')
    gelf_logger.info('{"username": "bar"}')
    gelf_logger.info('{"username": "baz"}')
    gelf_logger.info('{"username": "lol"}')

    parser = GELFParser()
    events = list(parser.parse(gelf_logger.handlers[0].stream.name, chunksize=1))
    assert len(events) == 4
    assert events[0] == '{"username": "foo"}'
    assert events[1] == '{"username": "bar"}'
    assert events[2] == '{"username": "baz"}'
    assert events[3] == '{"username": "lol"}'

    parser = GELFParser()
    events = list(parser.parse(gelf_logger.handlers[0].stream.name, chunksize=2))
    assert len(events) == 4
    assert events[0] == '{"username": "foo"}'
    assert events[1] == '{"username": "bar"}'
    assert events[2] == '{"username": "baz"}'
    assert events[3] == '{"username": "lol"}'

    parser = GELFParser()
    events = list(parser.parse(gelf_logger.handlers[0].stream.name, chunksize=10))
    assert len(events) == 4
    assert events[0] == '{"username": "foo"}'
    assert events[1] == '{"username": "bar"}'
    assert events[2] == '{"username": "baz"}'
    assert events[3] == '{"username": "lol"}'
