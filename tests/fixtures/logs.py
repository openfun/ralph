"""Logs format pytest fixtures."""

import logging
from secrets import token_hex
from tempfile import NamedTemporaryFile

import pytest
from logging_gelf.formatters import GELFFormatter


@pytest.fixture
def gelf_logger():
    """Generate a GELF logger to generate wrapped tracking log fixtures."""
    with NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        handler = logging.StreamHandler(temp_file)
        handler.setLevel(logging.INFO)
        handler.setFormatter(GELFFormatter(null_character=False))

        # Generate a unique logger per test function to avoid stacking handlers on
        # the same one
        logger = logging.getLogger(f"test_logger_{token_hex(8)}")
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        yield logger
