"""
Tests for ralph.parsers module.
"""
import gzip
import logging
import shutil

import pandas as pd
import pytest

from ralph import filters
from ralph.parsers import BaseParser, GELFParser


def test_baseparser_parse():
    """Test that calling parse on the BaseParser raises a NotImplementedError."""

    with pytest.raises(NotImplementedError):
        BaseParser().parse("foo.log")

    # pylint: disable=abstract-method
    class MyParser(BaseParser):
        """Dummy parser."""

    with pytest.raises(NotImplementedError):
        MyParser().parse("foo.log")


# pylint: disable=invalid-name
def test_gelfparser_parse_raw_file(fs, gelf_logger):
    """Test the GELFParser parsing using a flat GELF file."""

    parser = GELFParser()

    # Input log file does not exists
    with pytest.raises(OSError):
        parser.parse("/i/do/not/exist")

    # Input log file is empty
    empty_file_path = "/var/log/empty"
    fs.create_file(empty_file_path)
    events = parser.parse(empty_file_path)
    assert len(events) == 0
    assert events.equals(pd.DataFrame())

    # Create two log entries
    gelf_logger.info('{"username": "foo"}')
    gelf_logger.info('{"username": ""}')

    events = parser.parse(gelf_logger.handlers[0].stream.name)
    assert len(events) == 2
    assert events.equals(pd.DataFrame({"username": ["foo", ""]}))


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
    events = parser.parse(gzipped_log_file_name)
    assert len(events) == 2
    assert events.equals(pd.DataFrame({"username": ["foo", "bar"]}))


# pylint: disable=invalid-name,unused-argument
def test_gelfparser_parse_with_various_chunksizes(fs, gelf_logger):
    """Test the GELFParser parsing using different chunksizes."""

    gelf_logger.info('{"username": "foo"}')
    gelf_logger.info('{"username": "bar"}')

    parser = GELFParser()
    events = parser.parse(gelf_logger.handlers[0].stream.name, chunksize=1)
    assert len(events) == 2
    assert events.equals(pd.DataFrame({"username": ["foo", "bar"]}))

    events = parser.parse(gelf_logger.handlers[0].stream.name, chunksize=2)
    assert len(events) == 2
    assert events.equals(pd.DataFrame({"username": ["foo", "bar"]}))

    events = parser.parse(gelf_logger.handlers[0].stream.name, chunksize=10)
    assert len(events) == 2
    assert events.equals(pd.DataFrame({"username": ["foo", "bar"]}))


# pylint: disable=invalid-name,unused-argument
def test_gelfparser_parse_filtering_breaks_when_empty(fs, gelf_logger, caplog):
    """Test the GELFParser parsing filtering breaks when a chunk record is empty."""

    parser = GELFParser()
    log_file_name = gelf_logger.handlers[0].stream.name

    # -- Empty filter
    # Create an anonymous tracking log
    gelf_logger.info('{"username": ""}')
    # Reset captured logs so that we can focus on the warning log for empty
    # filtered records
    caplog.clear()
    # Anonymous filter + a lambda filter that should create a warning log
    # message
    with caplog.at_level(logging.WARNING, logger="ralph.parsers"):
        events = parser.parse(log_file_name, filters=[filters.anonymous, lambda pd: pd])
    assert caplog.record_tuples == [
        (
            "ralph.parsers",
            logging.WARNING,
            "Current chunk contains no records, will stop filtering.",
        )
    ]
    assert len(events) == 0
    assert events.empty


# pylint: disable=invalid-name,unused-argument
def test_gelfparser_parse_with_filters(fs, gelf_logger):
    """Test the GELFParser parsing with filters."""

    parser = GELFParser()
    log_file_name = gelf_logger.handlers[0].stream.name

    # -- Anonymous filter
    gelf_logger.info('{"username": "foo"}')
    gelf_logger.info('{"username": ""}')

    events = parser.parse(log_file_name, filters=[filters.anonymous])
    assert len(events) == 1
    assert events.equals(pd.DataFrame({"username": ["foo"]}))
