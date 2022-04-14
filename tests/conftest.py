"""
Module py.test fixtures
"""
# pylint: disable=unused-import

from .fixtures import hypothesis_configuration  # noqa: F401
from .fixtures import hypothesis_strategies  # noqa: F401
from .fixtures.backends import es, es_data_stream, events, swift, ws  # noqa: F401
from .fixtures.logs import gelf_logger  # noqa: F401
