"""Tests for the base ora event schema"""

# pylint: disable=redefined-outer-name
import pytest
from marshmallow import ValidationError

from tests.fixtures.logs import EventType, event_generator
from tests.schemas.edx.test_common import check_error


@pytest.fixture()
def base_ora_event():
    """Returns a base event generator that generates size number of events"""
    return lambda **kwargs: event_generator(EventType.BASE_ORA_EVENT, **kwargs)


def test_valid_username_should_not_raise_exception(base_ora_event):
    """Test that a valid base_ora_event does not raise a ValidationError"""
    try:
        base_ora_event()
        base_ora_event(username="valid username")
    except ValidationError:
        pytest.fail("Event with valid username should not raise exceptions")


def test_invalid_username_value(base_ora_event):
    """ValidationError should be raised if the username value
    is empty or less than 2 characters
    """
    with pytest.raises(ValidationError) as excinfo:
        base_ora_event(username="")
    check_error(excinfo, "Length must be between 2 and 30.", error_key="username")
    with pytest.raises(ValidationError):
        base_ora_event(username="1")
    check_error(excinfo, "Length must be between 2 and 30.", error_key="username")
    with pytest.raises(ValidationError):
        base_ora_event(username=1234)
    check_error(excinfo, "Length must be between 2 and 30.", error_key="username")
    with pytest.raises(ValidationError):
        base_ora_event(username="more_than_30_characters_long_for_sure")
    check_error(excinfo, "Length must be between 2 and 30.", error_key="username")


def test_invalid_page_value(base_ora_event):
    """ValidationError should be raised if the page value
    is not x_module
    """
    with pytest.raises(ValidationError) as excinfo:
        base_ora_event(page="not_x_module")
    check_error(excinfo, "The event page field is not `x_module`")
