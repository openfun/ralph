"""Tests for the base converter"""

import json
from typing import Any, Optional

import pytest
from pydantic.main import BaseModel

from ralph.exceptions import ConversionException
from ralph.models import converter as converter_module
from ralph.models.edx.converters.xapi.base import BaseConverter


@pytest.fixture(autouse=True)
def setup_edx_uuid_namespace(monkeypatch):
    """Monkeypatches the required EDX_UUID_NAMESPACE configuration."""

    uuid = "51f5c14e-0150-4766-88d2-6f7991ad6bfe"
    monkeypatch.setattr(converter_module, "EDX_UUID_NAMESPACE", uuid)


class DummyBaseConverter(BaseConverter):
    """Dummy implementation of abstract BaseConverter."""

    __model__ = BaseModel

    def get_conversion_set(self):  # pylint: disable=no-self-use
        """Returns a conversion set used for conversion."""

        return set()


@pytest.mark.parametrize("bad_uuid", [None, "invalid UUID"])
def test_models_converter_base_converter_get_event_uuid5_with_invalid_namespace(
    bad_uuid, monkeypatch
):
    """Tests the `get_event_uuid5` method should raise a ConversionException
    when the EDX_UUID_NAMESPACE is not set properly.
    """

    monkeypatch.setattr(converter_module, "EDX_UUID_NAMESPACE", bad_uuid)
    error = "Invalid EDX_UUID_NAMESPACE configuration."
    with pytest.raises(ConversionException, match=error):
        BaseConverter.get_event_uuid5("{}")


@pytest.mark.parametrize("event", [{}, {"foo": "bar"}])
def test_models_converter_base_converter_convert_with_empty_conversion_dictionary(
    event,
):
    """Tests when the conversion_dictionary is empty, convert should write an empty dictionary."""

    event_str = json.dumps(event)
    assert DummyBaseConverter().convert(event, event_str) == json.dumps({})


@pytest.mark.parametrize(
    "static_value",
    [
        123,
        "value",
        {"foo": "foo_value"},
        ["foo", "bar"],
    ],
)
def test_models_converter_base_converter_convert_with_static_value(
    static_value, monkeypatch
):
    """Tests the convert method with a conversion_set containing a static value."""

    conversion_set = {("static", lambda: static_value)}
    monkeypatch.setattr(
        DummyBaseConverter, "get_conversion_set", lambda _: conversion_set
    )

    class DummyBaseModel(BaseModel):
        """Dummy base model with one field."""

        static: Any

    monkeypatch.setattr(DummyBaseConverter, "__model__", DummyBaseModel)
    assert json.loads(DummyBaseConverter().convert({}, "{}")) == {
        "static": static_value
    }


@pytest.mark.parametrize(
    "source_transformer,expected",
    [
        # Puts the original "foo" value in the destination dict.
        (("foo",), {"converted": "foo_value"}),
        # Puts the transformed "foo" value in the destination dict.
        (("foo", lambda foo: foo.upper()), {"converted": "FOO_VALUE"}),
        # Ignores the "not_foo" value as it's not present in the source dict.
        (("not_foo",), {}),
    ],
)
def test_models_converter_base_converter_convert_with_source_transformer_tuples(
    source_transformer, expected, monkeypatch
):
    """Tests the convert method with a conversion_set containing source and transformer tuples."""

    event = {"foo": "foo_value", "bar": "bar_value"}
    event_str = json.dumps(event)
    conversion_set = {("converted",) + source_transformer}
    monkeypatch.setattr(
        DummyBaseConverter, "get_conversion_set", lambda _: conversion_set
    )

    class DummyBaseModel(BaseModel):
        """Dummy base model with one field."""

        converted: Optional[Any]

    monkeypatch.setattr(DummyBaseConverter, "__model__", DummyBaseModel)
    assert json.loads(DummyBaseConverter().convert(event, event_str)) == expected
