"""Module py.test fixtures."""

# pylint: disable=unused-import

from .fixtures import hypothesis_configuration  # noqa: F401
from .fixtures import hypothesis_strategies  # noqa: F401
from .fixtures.auth import (  # noqa: F401
    auth_credentials,
    basic_auth_test_client,
    encoded_token,
    mock_discovery_response,
    mock_oidc_jwks,
    oidc_auth_test_client,
)
from .fixtures.backends import (  # noqa: F401
    anyio_backend,
    clickhouse,
    clickhouse_backend,
    clickhouse_lrs_backend,
    es,
    es_backend,
    es_data_stream,
    es_forwarding,
    es_lrs_backend,
    events,
    fs_backend,
    ldp_backend,
    lrs,
    mongo,
    mongo_forwarding,
    moto_fs,
    s3,
    s3_backend,
    settings_fs,
    swift,
    swift_backend,
    ws,
)
from .fixtures.logs import gelf_logger  # noqa: F401
