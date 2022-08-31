"""
Module py.test fixtures
"""
# pylint: disable=unused-import

from .fixtures import hypothesis_configuration  # noqa: F401
from .fixtures import hypothesis_strategies  # noqa: F401
from .fixtures.auth import auth_credentials  # noqa: F401
from .fixtures.backends import (  # noqa: F401
    es,
    es_data_stream,
    es_forwarding,
    events,
    lrs,
    mongo,
    mongo_forwarding,
    swift,
    ws,
)
from .fixtures.logs import gelf_logger  # noqa: F401
