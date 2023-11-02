"""Configurations for Ralph backends."""

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from ralph.backends.data.clickhouse import ClickHouseDataBackendSettings
from ralph.backends.data.es import ESDataBackendSettings
from ralph.backends.data.fs import FSDataBackendSettings
from ralph.backends.data.ldp import LDPDataBackendSettings
from ralph.backends.data.mongo import MongoDataBackendSettings
from ralph.backends.data.s3 import S3DataBackendSettings
from ralph.backends.data.swift import SwiftDataBackendSettings
from ralph.backends.http.async_lrs import LRSHTTPBackendSettings
from ralph.backends.lrs.clickhouse import ClickHouseLRSBackendSettings
from ralph.backends.lrs.fs import FSLRSBackendSettings
from ralph.backends.stream.ws import WSStreamBackendSettings
from ralph.conf import BASE_SETTINGS_CONFIG, core_settings

# Active Data backend Settings.


class DataBackendSettings(BaseModel):
    """Pydantic model for data backend configuration settings."""

    ASYNC_ES: ESDataBackendSettings = ESDataBackendSettings()
    ASYNC_MONGO: MongoDataBackendSettings = MongoDataBackendSettings()
    CLICKHOUSE: ClickHouseDataBackendSettings = ClickHouseDataBackendSettings()
    ES: ESDataBackendSettings = ESDataBackendSettings()
    FS: FSDataBackendSettings = FSDataBackendSettings()
    LDP: LDPDataBackendSettings = LDPDataBackendSettings()
    MONGO: MongoDataBackendSettings = MongoDataBackendSettings()
    SWIFT: SwiftDataBackendSettings = SwiftDataBackendSettings()
    S3: S3DataBackendSettings = S3DataBackendSettings()


# Active HTTP backend Settings.


class HTTPBackendSettings(BaseModel):
    """Pydantic model for HTTP backend configuration settings."""

    LRS: LRSHTTPBackendSettings = LRSHTTPBackendSettings()


# Active LRS backend Settings.


class LRSBackendSettings(BaseModel):
    """Pydantic model for LRS compatible backend configuration settings."""

    ASYNC_ES: ESDataBackendSettings = ESDataBackendSettings()
    ASYNC_MONGO: MongoDataBackendSettings = MongoDataBackendSettings()
    CLICKHOUSE: ClickHouseLRSBackendSettings = ClickHouseLRSBackendSettings()
    ES: ESDataBackendSettings = ESDataBackendSettings()
    FS: FSLRSBackendSettings = FSLRSBackendSettings()
    MONGO: MongoDataBackendSettings = MongoDataBackendSettings()


# Active Stream backend Settings.


class StreamBackendSettings(BaseModel):
    """Pydantic model for stream backend configuration settings."""

    WS: WSStreamBackendSettings = WSStreamBackendSettings()


# Active backend Settings.


class Backends(BaseModel):
    """Pydantic model for backends configuration settings."""

    DATA: DataBackendSettings = DataBackendSettings()
    HTTP: HTTPBackendSettings = HTTPBackendSettings()
    LRS: LRSBackendSettings = LRSBackendSettings()
    STREAM: StreamBackendSettings = StreamBackendSettings()


class BackendSettings(BaseSettings):
    """Pydantic model for Ralph's backends environment & configuration settings."""

    # TODO[pydantic]: The `Config` class inherits from another class, please create the `model_config` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    # class Config(BaseSettingsConfig):
    #     """Pydantic Configuration."""

    #     env_file = ".env"
    #     env_file_encoding = core_settings.LOCALE_ENCODING

    model_config = BASE_SETTINGS_CONFIG | SettingsConfigDict(
        env_file=".env", env_file_encoding=core_settings.LOCALE_ENCODING
    )

    BACKENDS: Backends = Backends()


backends_settings = BackendSettings()
