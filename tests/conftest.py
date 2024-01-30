"""Module py.test fixtures."""


from .fixtures import (
    hypothesis_configuration,  # noqa: F401
    hypothesis_strategies,  # noqa: F401
)
from .fixtures.api import client  # noqa: F401
from .fixtures.auth import (  # noqa: F401
    basic_auth_credentials,
    encoded_token,
    mock_discovery_response,
    mock_oidc_jwks,
)
from .fixtures.backends import (  # noqa: F401
    anyio_backend,
    async_es_backend,
    async_es_lrs_backend,
    async_mongo_backend,
    async_mongo_lrs_backend,
    clickhouse,
    clickhouse_backend,
    clickhouse_custom,
    clickhouse_lrs_backend,
    es,
    es_backend,
    es_custom,
    es_data_stream,
    es_forwarding,
    es_lrs_backend,
    events,
    flavor,
    fs_backend,
    fs_lrs_backend,
    ldp_backend,
    lrs,
    lrs_backend,
    mongo,
    mongo_backend,
    mongo_custom,
    mongo_forwarding,
    mongo_lrs_backend,
    moto_fs,
    s3_backend,
    settings_fs,
    swift_backend,
    ws,
)
from .fixtures.logs import gelf_logger  # noqa: F401
