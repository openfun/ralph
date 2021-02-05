"""Tests for the BaseConverter class"""

import json

import pytest
from marshmallow import Schema

from ralph.schemas.edx.base import ContextModuleSchema, ContextSchema
from ralph.schemas.edx.converters.base import (
    BaseConverter,
    GetFromField,
    nested_del,
    nested_get,
    nested_set,
)

from tests.fixtures.logs import EventType


class DummyBaseConverter(BaseConverter):
    """Dummy implementation of abstract BaseConverter"""

    def get_conversion_dictionary(self):  # pylint: disable=no-self-use
        """Returns a conversion dictionary used for conversion."""
        return {}


BASE_CONVERTER = DummyBaseConverter()
CONTEXT_MODULE = {"display_name": "display_name_value", "usage_key": "usage_key_value"}


def get_patched_base_converter(conversion_dictionary, schema=ContextModuleSchema):
    """Returns a DummyBaseConverter that returns with given conversion_dictionary and schema"""

    # pylint: disable=protected-access, attribute-defined-outside-init
    DummyBaseConverter.get_conversion_dictionary = lambda self: conversion_dictionary
    base_converter = DummyBaseConverter()
    base_converter._schema = schema()
    return base_converter


def test_nested_get_should_return_given_value():
    """The nested_get function should return the value when it's present in the dictionary"""

    dictionary = {"foo": {"bar": "bar_value"}}
    assert nested_get(dictionary, ["foo", "bar"]) == "bar_value"


def test_nested_get_should_return_null_when_value_does_not_exists():
    """The nested_get function should return null if the value is not found"""

    dictionary = {"foo": {"bar": "bar_value"}}
    assert nested_get(dictionary, ["foo", "bar", "baz", "qux"]) is None
    assert nested_get(dictionary, ["foo", "not_bar"]) is None
    assert nested_get(dictionary, ["not_foo", "bar"]) is None
    assert nested_get(dictionary, None) is None


def test_nested_set_creating_new_fields():
    """When the fields are not present, nested_set should add them to the dictionary"""

    dictionary = {}
    nested_set(dictionary, ["foo", "bar"], "baz")
    assert dictionary == {"foo": {"bar": "baz"}}


def test_nested_set_updating_fields():
    """When the fields are present, nested_set should update them"""

    dictionary = {"foo": {"bar": "bar_value"}}
    nested_set(dictionary, ["foo", "bar"], "baz")
    assert dictionary == {"foo": {"bar": "baz"}}


def test_nested_del():
    """When the field is present, nested_del should remove it or stop silently"""

    # Field does not exists
    dictionary = {"foo": {"bar": "bar_value"}, "baz": "baz_value"}
    nested_del(dictionary, ["foo", "bar", "baz"])
    nested_del(dictionary, ["not_foo", "not_bar"])
    assert dictionary == {"foo": {"bar": "bar_value"}, "baz": "baz_value"}

    # Deleting field at first level
    nested_del(dictionary, ["foo"])
    assert dictionary == {"baz": "baz_value"}

    # Deleting nested field
    dictionary = {"foo": {"bar": "bar_value"}, "baz": "baz_value"}
    nested_del(dictionary, ["foo", "bar"])
    assert dictionary == {"foo": {}, "baz": "baz_value"}


@pytest.mark.parametrize(
    "field,args,expected_value",
    [
        ("", [], ""),
        ("some value", [], "some value"),
        ("uppercase", [lambda x: x.upper()], "UPPERCASE"),
    ],
)  # pylint: disable=too-many-arguments
def test_get_from_field(field, args, expected_value):
    """Check that for the specified arguments, we get the expected path and value"""

    get_from_field = GetFromField("some>path", *args)
    assert get_from_field.path == ["some", "path"]
    event = {"some": {"path": field}}
    assert get_from_field.value(event) == expected_value


def test_convert_with_empty_conversion_table():
    """When the conversion table is empty, convert should write an empty dictionary"""

    # pylint: disable=protected-access, attribute-defined-outside-init
    assert BASE_CONVERTER.convert({}) == json.dumps({})
    BASE_CONVERTER._schema = ContextModuleSchema()
    assert BASE_CONVERTER.convert(CONTEXT_MODULE) == json.dumps({})


def test_convert_with_failing_schema_validation():
    """Check the convert function don't write to file when the event is not valid"""

    # pylint: disable=protected-access, attribute-defined-outside-init
    BASE_CONVERTER._schema = Schema()
    assert BASE_CONVERTER.convert({"Not": "empty"}) is None

    BASE_CONVERTER._schema = ContextModuleSchema()
    context_module = {}
    assert BASE_CONVERTER.convert(context_module) is None

    context_module["display_name"] = "display_name_value"
    assert BASE_CONVERTER.convert(context_module) is None


@pytest.mark.parametrize(
    "static_value",
    [
        123,
        "value",
        {"foo": "foo_value"},
        ["foo", "bar"],
    ],
)
def test_convert_with_succeeding_schema_validation_and_static_values(static_value):
    """Conversion dictionary with a static values keeps the static values"""

    base_converter = get_patched_base_converter({"static": static_value})
    assert base_converter.convert(CONTEXT_MODULE) == json.dumps(
        {"static": static_value}
    )


def test_convert_with_succeeding_schema_validation_and_get_from_field_value():
    """Conversion dictionary with GetFromField objects gets their value"""

    # By default we get the field from the event and put it `as it is` in the converted event
    conversion_dictionary = {"get_from_field": GetFromField("usage_key")}
    base_converter = get_patched_base_converter(conversion_dictionary)
    assert base_converter.convert(CONTEXT_MODULE) == json.dumps(
        {"get_from_field": "usage_key_value"}
    )

    # When we want to transform the original value we use a lambda function for that
    conversion_dictionary["get_from_field_with_function"] = GetFromField(
        "usage_key", lambda usage_key: usage_key.upper()
    )
    base_converter = get_patched_base_converter(conversion_dictionary)
    assert base_converter.convert(CONTEXT_MODULE) == json.dumps(
        {
            "get_from_field": "usage_key_value",
            "get_from_field_with_function": "USAGE_KEY_VALUE",
        }
    )


def test_convert_with_nested_fields(event):
    """Check the convert function for a schema with nested fields"""

    # Create the context dictionary and conversion_dict
    context = event(EventType.SERVER)["context"]
    context["module"] = CONTEXT_MODULE
    course_id = context["course_id"]
    context[
        "path"
    ] = f"/courses/{course_id}/xblock/{CONTEXT_MODULE['usage_key']}/handler/"
    conversion_dictionary = {
        "new_path": GetFromField("path", lambda path: path.upper()),
        "nested": {
            "new_usage_key": GetFromField("module>usage_key"),
            "nested": {
                "new_display_name": GetFromField("module>display_name"),
                "static": "value",
            },
        },
    }
    # Create the converter and run test
    base_converter = get_patched_base_converter(conversion_dictionary, ContextSchema)
    assert base_converter.convert(context) == json.dumps(
        {
            "new_path": context["path"].upper(),
            "nested": {
                "new_usage_key": context["module"]["usage_key"],
                "nested": {
                    "new_display_name": context["module"]["display_name"],
                    "static": "value",
                },
            },
        }
    )
