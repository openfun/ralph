"""
Module py.test fixtures
"""
# pylint: disable=unused-import

from .fixtures.backends import es, swift  # noqa: F401
from .fixtures.logs import event, gelf_logger  # noqa: F401
