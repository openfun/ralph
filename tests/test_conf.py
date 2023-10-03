"""Tests for Ralph's configuration loading."""

from importlib import reload
from inspect import signature
from pathlib import PosixPath

import pytest
from pydantic import ValidationError

from ralph import conf
from ralph.conf import CommaSeparatedTuple, Settings, settings
from ralph.exceptions import ConfigurationException
from ralph.utils import import_string


def test_conf_settings_field_value_priority(fs, monkeypatch):
    """Test that the Settings object field values are defined in the following
    descending order of priority:

        1. Arguments passed to the initializer.
        2. Environment variables.
        3. Dotenv variables (.env)
        4. Default values.
    """
    # pylint: disable=invalid-name

    # 4. Using default value.
    assert str(Settings().AUTH_FILE) == str(settings.APP_DIR / "auth.json")

    # 3. Using dotenv variables (overrides default value).
    fs.create_file(".env", contents="RALPH_AUTH_FILE=/dotenv\n")
    assert str(Settings().AUTH_FILE) == "/dotenv"

    # 2. Using environment variable value (overrides dotenv value).
    monkeypatch.setenv("RALPH_AUTH_FILE", "/environment")
    assert str(Settings().AUTH_FILE) == "/environment"

    # 1. Using argument value (overrides environment value).
    assert str(Settings(AUTH_FILE="/argument").AUTH_FILE) == "/argument"


@pytest.mark.parametrize(
    "value,expected",
    [("foo", ("foo",)), (("foo",), ("foo",)), ("foo,bar,baz", ("foo", "bar", "baz"))],
)
def test_conf_comma_separated_list_with_valid_values(value, expected, monkeypatch):
    """Test the CommaSeparatedTuple pydantic data type with valid values."""
    assert next(CommaSeparatedTuple.__get_validators__())(value) == expected
    monkeypatch.setenv("RALPH_BACKENDS__DATABASE__ES__HOSTS", "".join(value))
    assert Settings().BACKENDS.DATABASE.ES.HOSTS == expected


@pytest.mark.parametrize("value", [{}, [], None])
def test_conf_comma_separated_list_with_invalid_values(value):
    """Test the CommaSeparatedTuple pydantic data type with invalid values."""
    with pytest.raises(TypeError, match="Invalid comma separated list"):
        next(CommaSeparatedTuple.__get_validators__())(value)


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
            "RALPH_BACKENDS__DATABASE__ES__CLIENT_OPTIONS__ca_certs", f"{ca_certs}"
        )
    # Using None here as in "not set by user"
    if verify_certs is not None:
        monkeypatch.setenv(
            "RALPH_BACKENDS__DATABASE__ES__CLIENT_OPTIONS__verify_certs",
            f"{verify_certs}",
        )
    assert Settings().BACKENDS.DATABASE.ES.CLIENT_OPTIONS.dict() == expected


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
        "RALPH_BACKENDS__DATABASE__ES__CLIENT_OPTIONS__ca_certs", f"{ca_certs}"
    )
    monkeypatch.setenv(
        "RALPH_BACKENDS__DATABASE__ES__CLIENT_OPTIONS__verify_certs",
        f"{verify_certs}",
    )
    with pytest.raises(ValidationError, match="1 validation error for"):
        Settings().BACKENDS.DATABASE.ES.CLIENT_OPTIONS.dict()


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
            "RALPH_BACKENDS__DATABASE__MONGO__CLIENT_OPTIONS__document_class",
            f"{document_class}",
        )
    # Using None here as in "not set by user"
    if tz_aware is not None:
        monkeypatch.setenv(
            "RALPH_BACKENDS__DATABASE__MONGO__CLIENT_OPTIONS__tz_aware",
            f"{tz_aware}",
        )
    assert Settings().BACKENDS.DATABASE.MONGO.CLIENT_OPTIONS.dict() == expected


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
        "RALPH_BACKENDS__DATABASE__MONGO__CLIENT_OPTIONS__document_class",
        f"{document_class}",
    )
    monkeypatch.setenv(
        "RALPH_BACKENDS__DATABASE__MONGO__CLIENT_OPTIONS__tz_aware",
        f"{tz_aware}",
    )
    with pytest.raises(ValidationError, match="1 validation error for"):
        Settings().BACKENDS.DATABASE.MONGO.CLIENT_OPTIONS.dict()


def test_conf_settings_should_define_all_backends_options():
    """Test that Settings model defines all backends options."""
    for _, backends in settings.BACKENDS:
        for _, backend in backends:
            # pylint: disable=protected-access
            backend_class = import_string(backend._class_path)
            for parameter in signature(backend_class.__init__).parameters.values():
                if parameter.name == "self":
                    continue
                assert hasattr(backend, parameter.name.upper())


def test_conf_core_settings_should_impact_settings_defaults(monkeypatch):
    """Test that core settings update application settings values."""
    monkeypatch.setenv("RALPH_APP_DIR", "/foo")
    monkeypatch.setenv("RALPH_LOCALE_ENCODING", "ascii")
    reload(conf)

    # Configuration.
    assert conf.Settings.Config.env_file_encoding == "ascii"

    # Properties.
    assert str(conf.settings.APP_DIR) == "/foo"
    assert conf.settings.LOCALE_ENCODING == "ascii"

    # Defaults.
    assert str(conf.settings.AUTH_FILE) == "/foo/auth.json"
    assert conf.settings.BACKENDS.STORAGE.FS.PATH == "/foo/archives"


def test_conf_forbidden_scopes_without_authority(monkeypatch):
    """Test that using RESTRICT_BY_SCOPES without RESTRICT_BY_AUTHORITY raises an
    error."""

    monkeypatch.setenv("RALPH_LRS_RESTRICT_BY_AUTHORITY", False)
    monkeypatch.setenv("RALPH_LRS_RESTRICT_BY_SCOPES", True)

    with pytest.raises(
        ConfigurationException,
        match=(
            "`LRS_RESTRICT_BY_AUTHORITY` must be set to `True` if using "
            "`LRS_RESTRICT_BY_SCOPES=True`"
        ),
    ):
        reload(conf)
