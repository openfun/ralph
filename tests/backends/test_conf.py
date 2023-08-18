"""Tests for Ralph's backends configuration loading."""

from pathlib import PosixPath

import pytest
from pydantic import ValidationError

from ralph.backends.conf import Backends, BackendSettings, DataBackendSettings
from ralph.backends.data.es import ESDataBackendSettings


def test_conf_settings_field_value_priority(fs, monkeypatch):
    """Test that the BackendSettings object field values are defined in the following
    descending order of priority:

        1. Arguments passed to the initializer.
        2. Environment variables.
        3. Dotenv variables (.env)
        4. Default values.
    """
    # pylint: disable=invalid-name

    # 4. Using default value.
    assert str(BackendSettings().BACKENDS.DATA.ES.LOCALE_ENCODING) == "utf8"

    # 3. Using dotenv variables (overrides default value).
    fs.create_file(".env", contents="RALPH_BACKENDS__DATA__ES__LOCALE_ENCODING=toto\n")
    assert str(BackendSettings().BACKENDS.DATA.ES.LOCALE_ENCODING) == "toto"

    # 2. Using environment variable value (overrides dotenv value).
    monkeypatch.setenv("RALPH_BACKENDS__DATA__ES__LOCALE_ENCODING", "foo")
    assert str(BackendSettings().BACKENDS.DATA.ES.LOCALE_ENCODING) == "foo"

    # 1. Using argument value (overrides environment value).
    assert (
        str(
            BackendSettings(
                BACKENDS=Backends(
                    DATA=DataBackendSettings(
                        ES=ESDataBackendSettings(LOCALE_ENCODING="bar")
                    )
                )
            ).BACKENDS.DATA.ES.LOCALE_ENCODING
        )
        == "bar"
    )


@pytest.mark.parametrize(
    "ca_certs,verify_certs,expected",
    [
        ("/path", "True", {"ca_certs": PosixPath("/path"), "verify_certs": True}),
        ("/path2", "f", {"ca_certs": PosixPath("/path2"), "verify_certs": False}),
        (None, None, {"ca_certs": None, "verify_certs": None}),
    ],
)
def test_conf_es_client_options_with_valid_values(
    ca_certs, verify_certs, expected, monkeypatch
):
    """Test the ESClientOptions pydantic data type with valid values."""
    # Using None here as in "not set by user"
    if ca_certs is not None:
        monkeypatch.setenv(
            "RALPH_BACKENDS__DATA__ES__CLIENT_OPTIONS__ca_certs", f"{ca_certs}"
        )
    # Using None here as in "not set by user"
    if verify_certs is not None:
        monkeypatch.setenv(
            "RALPH_BACKENDS__DATA__ES__CLIENT_OPTIONS__verify_certs",
            f"{verify_certs}",
        )
    assert BackendSettings().BACKENDS.DATA.ES.CLIENT_OPTIONS.dict() == expected


@pytest.mark.parametrize(
    "ca_certs,verify_certs",
    [
        ("/path", 3),
        ("/path", None),
    ],
)
def test_conf_es_client_options_with_invalid_values(
    ca_certs, verify_certs, monkeypatch
):
    """Test the ESClientOptions pydantic data type with invalid values."""
    monkeypatch.setenv(
        "RALPH_BACKENDS__DATA__ES__CLIENT_OPTIONS__ca_certs", f"{ca_certs}"
    )
    monkeypatch.setenv(
        "RALPH_BACKENDS__DATA__ES__CLIENT_OPTIONS__verify_certs",
        f"{verify_certs}",
    )
    with pytest.raises(ValidationError, match="1 validation error for"):
        BackendSettings().BACKENDS.DATA.ES.CLIENT_OPTIONS.dict()


@pytest.mark.parametrize(
    "document_class,tz_aware,expected",
    [
        ("dict", "True", {"document_class": "dict", "tz_aware": True}),
        ("str", "f", {"document_class": "str", "tz_aware": False}),
        (None, None, {"document_class": None, "tz_aware": None}),
    ],
)
def test_conf_mongo_client_options_with_valid_values(
    document_class, tz_aware, expected, monkeypatch
):
    """Test the MongoClientOptions pydantic data type with valid values."""
    # Using None here as in "not set by user"
    if document_class is not None:
        monkeypatch.setenv(
            "RALPH_BACKENDS__DATA__MONGO__CLIENT_OPTIONS__document_class",
            f"{document_class}",
        )
    # Using None here as in "not set by user"
    if tz_aware is not None:
        monkeypatch.setenv(
            "RALPH_BACKENDS__DATA__MONGO__CLIENT_OPTIONS__tz_aware",
            f"{tz_aware}",
        )
    assert BackendSettings().BACKENDS.DATA.MONGO.CLIENT_OPTIONS.dict() == expected


@pytest.mark.parametrize(
    "document_class,tz_aware",
    [
        ("dict", 3),
        ("str", None),
    ],
)
def test_conf_mongo_client_options_with_invalid_values(
    document_class, tz_aware, monkeypatch
):
    """Test the MongoClientOptions pydantic data type with invalid values."""
    monkeypatch.setenv(
        "RALPH_BACKENDS__DATA__MONGO__CLIENT_OPTIONS__document_class",
        f"{document_class}",
    )
    monkeypatch.setenv(
        "RALPH_BACKENDS__DATA__MONGO__CLIENT_OPTIONS__tz_aware",
        f"{tz_aware}",
    )
    with pytest.raises(ValidationError, match="1 validation error for"):
        BackendSettings().BACKENDS.DATA.MONGO.CLIENT_OPTIONS.dict()
