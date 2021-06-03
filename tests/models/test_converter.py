"""Tests for converter method"""

from typing import Any, Optional

import pytest
from pydantic import BaseModel

from ralph.exceptions import BadFormatException, ConversionException
from ralph.models.converter import ConversionItem, convert_dict_event, convert_str_event
from ralph.models.edx.converters.xapi.base import BaseConversionSet


@pytest.mark.parametrize(
    "conversion_item,expected_dest,expected_src,expected_transfomers,expected_raw_input",
    [
        (
            ConversionItem("destination", "source"),
            ("destination",),
            ("source",),
            (lambda _: _,),
            False,
        ),
        (
            ConversionItem("destination", raw_input=True),
            ("destination",),
            None,
            (lambda _: _,),
            True,
        ),
        (
            ConversionItem("destination__nested", "source__nested", lambda x: x + x),
            ("destination", "nested"),
            ("source", "nested"),
            (lambda x: x + x,),
            False,
        ),
        (
            ConversionItem("destination__nested", None, (lambda x: x + x, lambda x: x)),
            ("destination", "nested"),
            None,
            (lambda x: x + x, lambda x: x),
            False,
        ),
    ],
)
def test_converter_conversion_item_initialization(
    conversion_item,
    expected_dest,
    expected_src,
    expected_transfomers,
    expected_raw_input,
):
    """Tests the ConversionItem initialization."""

    assert conversion_item.dest == expected_dest
    assert conversion_item.src == expected_src
    for i, expected_transfomer in enumerate(expected_transfomers):
        current_transformer_code = conversion_item.transformers[i].__code__.co_code
        assert current_transformer_code == expected_transfomer.__code__.co_code
    assert conversion_item.raw_input == expected_raw_input


@pytest.mark.parametrize("event", [{"foo": "bar", "baz": {"qux": "quux"}}])
@pytest.mark.parametrize(
    "conversion_item,expected",
    [
        (ConversionItem("", "foo"), "bar"),
        (ConversionItem("", "foo", str.upper), "BAR"),
        (ConversionItem("", "foo", [str.upper, str.islower]), False),
        (ConversionItem("", "baz__qux"), "quux"),
        (ConversionItem("", "baz__qux__bad"), None),
        (ConversionItem("", "not_found"), None),
        (ConversionItem("", "not_found", lambda _: "foobar"), "foobar"),
        (ConversionItem(""), {"foo": "bar", "baz": {"qux": "quux"}}),
        (ConversionItem("", None, lambda event: event["foo"]), "bar"),
    ],
)
def test_converter_conversion_item_get_value_with_successful_transformers(
    event, conversion_item, expected
):
    """Tests that the get_value method returns the expected value."""

    assert conversion_item.get_value(event) == expected


@pytest.mark.parametrize("event", [{}, {"foo": "bar"}])
def test_converter_convert_dict_event_with_empty_conversion_set(event):
    """Tests when the conversion_set is empty, convert_dict_event should return an empty model."""

    class DummyBaseConversionSet(BaseConversionSet):
        """Dummy implementation of abstract BaseConversionSet."""

        __dest__ = BaseModel

        def _get_conversion_items(self):  # pylint: disable=no-self-use
            """Returns a set of ConversionItems used for conversion."""

            return set()

    assert convert_dict_event(event, "", DummyBaseConversionSet()).dict() == {}


@pytest.mark.parametrize("event", [{"foo": "foo_value", "bar": "bar_value"}])
@pytest.mark.parametrize(
    "source,transformer,expected",
    [
        # Puts the original "foo" value in the destination dict.
        ("foo", lambda x: x, {"converted": "foo_value"}),
        # Puts the transformed "foo" value in the destination dict.
        ("foo", lambda foo: foo.upper(), {"converted": "FOO_VALUE"}),
        # Ignores the "not_foo" value as it's not present in the source dict.
        ("not_foo", lambda x: x, {}),
        # Passes the whole event to the transformers
        (None, (str, len), {"converted": 40}),
        # Returns a static value
        (None, lambda _: "static", {"converted": "static"}),
    ],
)
def test_converter_convert_dict_event_with_one_conversion_item(
    event, source, transformer, expected
):
    """Tests the convert_dict_event method with a conversion_set containing one conversion item."""

    class DummyBaseModel(BaseModel):
        """Dummy base model with one field."""

        converted: Optional[Any]

    class DummyBaseConversionSet(BaseConversionSet):
        """Dummy implementation of abstract BaseConversionSet."""

        __dest__ = DummyBaseModel

        def _get_conversion_items(self):  # pylint: disable=no-self-use
            """Returns a set of ConversionItems used for conversion."""

            return {ConversionItem("converted", source, transformer)}

    converted = convert_dict_event(event, "", DummyBaseConversionSet())
    assert converted.dict(exclude_none=True) == expected


@pytest.mark.parametrize("item", [ConversionItem("foo", None, lambda x: x / 0)])
def test_converter_convert_dict_event_with_one_conversion_item_raising_an_exception(
    item,
):
    """Tests that the convert_dict_event method raises a ConversionException."""

    class DummyBaseConversionSet(BaseConversionSet):
        """Dummy implementation of abstract BaseConversionSet."""

        __dest__ = BaseModel

        def _get_conversion_items(self):  # pylint: disable=no-self-use
            """Returns a set of ConversionItems used for conversion."""

            return {item}

    msg = "Failed to get the transformed value for field: None"
    with pytest.raises(ConversionException, match=msg):
        convert_dict_event({}, "{}", DummyBaseConversionSet())


@pytest.mark.parametrize("invalid_json", [""])
def test_converter_convert_str_event_with_invalid_json_string(invalid_json):
    """Tests that the convert_str_event method raises a BadFormatException."""

    class DummyBaseConversionSet(BaseConversionSet):
        """Dummy implementation of abstract BaseConversionSet."""

        __dest__ = BaseModel

        def _get_conversion_items(self):  # pylint: disable=no-self-use
            """Returns a set of ConversionItems used for conversion."""

            return set()

    msg = "Failed to parse the event, invalid JSON string"
    with pytest.raises(BadFormatException, match=msg):
        convert_str_event(invalid_json, DummyBaseConversionSet())
