"""
Module py.test fixtures
"""
# pylint: disable=unused-import

from .fixtures.backends import es, es_data_stream, events, swift, ws  # noqa: F401
from .fixtures.logs import gelf_logger  # noqa: F401
