"""Tests for converter method."""

import json
import logging
from typing import Any, Optional

import pytest
from hypothesis import HealthCheck, settings
from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError

from ralph.exceptions import (
    BadFormatException,
    ConversionException,
    MissingConversionSetException,
    UnknownEventException,
)
from ralph.models.converter import (
    ConversionItem,
    Converter,
    convert_dict_event,
    convert_str_event,
)
from ralph.models.edx.converters.xapi.base import BaseConversionSet
from ralph.models.edx.navigational.statements import UIPageClose
from ralph.models.xapi.constants import VERB_TERMINATED_ID

from tests.fixtures.hypothesis_strategies import custom_given


@pytest.mark.parametrize(
    (
        "conversion_item,expected_dest,expected_src,expected_transfomers,"
        "expected_raw_input"
    ),
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
    """Tests when the conversion_set is empty, convert_dict_event should return an empty
    model.
    """

    class DummyBaseConversionSet(BaseConversionSet):
        """Dummy implementation of abstract BaseConversionSet."""

        __dest__ = BaseModel

        def _get_conversion_items(self):  # pylint: disable=no-self-use
            """Returns a set of ConversionItems used for conversion."""
            return set()

    assert not convert_dict_event(event, "", DummyBaseConversionSet()).dict()


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
    """Tests the convert_dict_event method with a conversion_set containing one
    conversion item.
    """

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


@pytest.mark.parametrize("valid_uuid", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_converter_converter_convert_with_no_events(caplog, valid_uuid):
    """Tests given no events the convert method does not write error messages."""
    result = Converter(platform_url="", uuid_namespace=valid_uuid).convert(
        [], ignore_errors=False, fail_on_unknown=True
    )
    with caplog.at_level(logging.ERROR):
        assert not list(result)
    assert [] == [message for _, _, message in caplog.record_tuples]


@pytest.mark.parametrize("event", ["", 1, None, {}])
@pytest.mark.parametrize("valid_uuid", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_converter_convert_with_a_non_json_event_writes_an_error_message(
    event, valid_uuid, caplog
):
    """Tests given a non JSON event, the convert method should write an error
    message.
    """
    result = Converter(platform_url="", uuid_namespace=valid_uuid).convert(
        [event], ignore_errors=True, fail_on_unknown=True
    )
    with caplog.at_level(logging.ERROR):
        assert not list(result)
    errors = ["Input event is not a valid JSON string"]
    assert errors == [message for _, _, message in caplog.record_tuples]


@pytest.mark.parametrize("event", ["", 1, None, {}])
@pytest.mark.parametrize("valid_uuid", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_converter_convert_with_a_non_json_event_raises_an_exception(
    event, valid_uuid, caplog
):
    """Tests given a non JSON event, the convert method should raise a
    BadFormatException.
    """
    result = Converter(platform_url="", uuid_namespace=valid_uuid).convert(
        [event], ignore_errors=False, fail_on_unknown=True
    )
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BadFormatException):
            list(result)


@pytest.mark.parametrize(
    "event",
    [
        json.dumps({}),
        json.dumps({"event_source": "browser"}),
        json.dumps({"event_source": "browser", "event_type": None}),
    ],
)
@pytest.mark.parametrize("valid_uuid", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_converter_convert_with_an_unknown_event_writes_an_error_message(
    event, valid_uuid, caplog
):
    """Tests given an unknown event the convert method should write an error
    message.
    """
    result = Converter(platform_url="", uuid_namespace=valid_uuid).convert(
        [event], ignore_errors=False, fail_on_unknown=False
    )
    with caplog.at_level(logging.ERROR):
        assert not list(result)
    errors = ["No matching pydantic model found for input event"]
    assert errors == [message for _, _, message in caplog.record_tuples]


@pytest.mark.parametrize(
    "event",
    [
        json.dumps({}),
        json.dumps({"event_source": "browser"}),
        json.dumps({"event_source": "browser", "event_type": None}),
    ],
)
@pytest.mark.parametrize("valid_uuid", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_converter_convert_with_an_unknown_event_raises_an_exception(
    event, valid_uuid, caplog
):
    """Tests given an unknown event the convert method should raise an
    UnknownEventException.
    """
    result = Converter(platform_url="", uuid_namespace=valid_uuid).convert(
        [event], ignore_errors=False, fail_on_unknown=True
    )
    with caplog.at_level(logging.ERROR):
        with pytest.raises(UnknownEventException):
            list(result)


# pylint: disable=line-too-long
@pytest.mark.parametrize(
    "event",
    [json.dumps({"event_source": "browser", "event_type": "page_close"})],
)
@pytest.mark.parametrize("valid_uuid", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_converter_convert_with_an_event_missing_a_conversion_set_writes_an_error_message(  # noqa
    event, valid_uuid, caplog
):
    """Tests given an event that doesn't have a corresponding conversion_set, the
    convert method should write an error message.
    """
    result = Converter(module="os", platform_url="", uuid_namespace=valid_uuid).convert(
        [event], ignore_errors=False, fail_on_unknown=False
    )
    with caplog.at_level(logging.ERROR):
        assert not list(result)
    errors = ["No conversion set found for input event"]
    assert errors == [message for _, _, message in caplog.record_tuples]


@pytest.mark.parametrize(
    "event",
    [json.dumps({"event_source": "browser", "event_type": "page_close"})],
)
@pytest.mark.parametrize("valid_uuid", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_converter_convert_with_an_event_missing_a_conversion_set_raises_an_exception(
    event, valid_uuid, caplog
):
    """Tests given an event that doesn't have a corresponding conversion_set, the
    convert method should raise a MissingConversionSetException.
    """
    result = Converter(module="os", platform_url="", uuid_namespace=valid_uuid).convert(
        [event], ignore_errors=False, fail_on_unknown=True
    )
    with caplog.at_level(logging.ERROR):
        with pytest.raises(MissingConversionSetException):
            list(result)


# pylint: disable=line-too-long
@pytest.mark.parametrize(
    "event",
    [json.dumps({"event_source": "browser", "event_type": "page_close"})],
)
@pytest.mark.parametrize("valid_uuid", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_converter_convert_with_an_invalid_page_close_event_writes_an_error_message(  # noqa
    event,
    valid_uuid,
    caplog,
):
    """Tests given an event that matches a pydantic model but fails at the conversion
    step, the convert method should write an error message.
    """
    result = Converter(platform_url="", uuid_namespace=valid_uuid).convert(
        [event], ignore_errors=True, fail_on_unknown=True
    )
    with caplog.at_level(logging.ERROR):
        assert not list(result)
    errors = ["Failed to get the transformed value for field: ('context', 'course_id')"]
    assert errors == [message for _, _, message in caplog.record_tuples]


@pytest.mark.parametrize(
    "event",
    [json.dumps({"event_source": "browser", "event_type": "page_close"})],
)
@pytest.mark.parametrize("valid_uuid", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_converter_convert_with_invalid_page_close_event_raises_an_exception(
    event, valid_uuid, caplog
):
    """Tests given an event that matches a pydantic model but fails at the conversion
    step, the convert method should raise a ConversionException.
    """
    result = Converter(platform_url="", uuid_namespace=valid_uuid).convert(
        [event], ignore_errors=False, fail_on_unknown=True
    )
    with caplog.at_level(logging.ERROR):
        with pytest.raises(ConversionException):
            list(result)


@settings(suppress_health_check=(HealthCheck.function_scoped_fixture,))
@pytest.mark.parametrize("valid_uuid", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
@pytest.mark.parametrize("invalid_platform_url", ["", "not an URL"])
@custom_given(UIPageClose)
def test_converter_convert_with_invalid_arguments_writes_an_error_message(
    valid_uuid, invalid_platform_url, caplog, event
):
    """Tests given invalid arguments causing the conversion to fail at the validation
    step, the convert method should write an error message.
    """
    event_str = event.json()
    result = Converter(
        platform_url=invalid_platform_url, uuid_namespace=valid_uuid
    ).convert([event_str], ignore_errors=True, fail_on_unknown=True)
    with caplog.at_level(logging.ERROR):
        assert not list(result)
    model_name = "<class 'ralph.models.xapi.navigation.statements.PageTerminated'>"
    errors = f"Converted event is not a valid ({model_name}) model"
    for _, _, message in caplog.record_tuples:
        assert errors == message


@settings(suppress_health_check=(HealthCheck.function_scoped_fixture,))
@pytest.mark.parametrize("valid_uuid", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
@pytest.mark.parametrize("invalid_platform_url", ["", "not an URL"])
@custom_given(UIPageClose)
def test_converter_convert_with_invalid_arguments_raises_an_exception(
    valid_uuid, invalid_platform_url, caplog, event
):
    """Tests given invalid arguments causing the conversion to fail at the validation
    step, the convert method should raise a ValidationError.
    """
    event_str = event.json()
    result = Converter(
        platform_url=invalid_platform_url, uuid_namespace=valid_uuid
    ).convert([event_str], ignore_errors=False, fail_on_unknown=True)
    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValidationError):
            list(result)


@pytest.mark.parametrize("ignore_errors", [True, False])
@pytest.mark.parametrize("fail_on_unknown", [True, False])
@pytest.mark.parametrize("valid_uuid", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
@custom_given(UIPageClose)
def test_converter_convert_with_valid_events(
    ignore_errors, fail_on_unknown, valid_uuid, event
):
    """Tests given a valid event the convert method should yield it."""
    event_str = event.json()
    result = Converter(
        platform_url="https://fun-mooc.fr", uuid_namespace=valid_uuid
    ).convert([event_str], ignore_errors, fail_on_unknown)
    assert json.loads(next(result))["verb"]["id"] == VERB_TERMINATED_ID.__args__[0]


@settings(suppress_health_check=(HealthCheck.function_scoped_fixture,))
@custom_given(UIPageClose)
@pytest.mark.parametrize("valid_uuid", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_converter_convert_counter(valid_uuid, caplog, event):
    """Tests given multiple events the convert method should log the total and invalid
    events.
    """
    valid_event = event.json()
    invalid_event_1 = 1
    invalid_event_2 = ""
    events = [invalid_event_1, valid_event, invalid_event_2]
    result = Converter(
        platform_url="https://fun-mooc.fr", uuid_namespace=valid_uuid
    ).convert(events, ignore_errors=True, fail_on_unknown=False)
    with caplog.at_level(logging.INFO):
        assert len(list(result)) == 1
    assert (
        "ralph.models.converter",
        logging.INFO,
        "Total events: 3, Invalid events: 2",
    ) in caplog.record_tuples
