"""
Tests for the base event schema
"""
# pylint: disable=redefined-outer-name
import operator

import pandas as pd
import pytest
from marshmallow import ValidationError

from tests.fixtures.logs import EventType, _event

from .test_common import check_error

BULK_EVENTS = _event(50, EventType.BASE_EVENT)


@pytest.fixture()
def base_event():
    """Returns a base event generator that generates size number of events"""
    return lambda size=1, **kwargs: _event(size, EventType.BASE_EVENT, **kwargs)


def test_valid_ip_should_not_raise_exception(base_event):
    """Test that a valid ip address does not raise a ValidationError"""
    try:
        base_event(ip="51.255.9.27")
        base_event(ip="8.8.8.8")
        base_event(ip="")
    except ValidationError:
        pytest.fail("Valid base event ip address should not raise exceptions")


def test_invalid_ip_should_raise_exception(base_event):
    """Test that a invalid ip addresse raise ValidationError"""
    with pytest.raises(ValidationError) as excinfo:
        base_event(ip="invalid_ip")
    check_error(excinfo, "Invalid IPv4 Address")
    with pytest.raises(ValidationError) as excinfo:
        base_event(ip="  ")
    check_error(excinfo, "Invalid IPv4 Address")


def test_empty_fields_should_not_raise_exception(base_event):
    """Test that an empty agent / host / referer / accept_language
    does not raise ValidationError
    """
    try:
        base_event(agent="")
        base_event(host="")
        base_event(referer="")
    except ValidationError:
        pytest.fail("Valid base event agent field should not raise exceptions")


def test_event_source_should_be_server(base_event):
    """Test that the event_source is equal to `server` and if not the
    event is invalid and should raise a ValidationException
    """
    event = base_event()
    assert event.iloc[0]["event_source"] == "server"
    with pytest.raises(ValidationError) as excinfo:
        base_event(event_source="not_server")
    check_error(excinfo, "The event event_source field is not `server`")


def test_page_should_be_none(base_event):
    """Test that the page is equal to `None` and if not the
    event is invalid and should rais a ValidationError
    """
    event = base_event()
    assert event.iloc[0]["page"] is None
    with pytest.raises(ValidationError) as excinfo:
        base_event(page="not_None")
    check_error(excinfo, "The event page field is not None")
    with pytest.raises(ValidationError) as excinfo:
        base_event(page=0)
    check_error(excinfo, "Not a valid string.")
    with pytest.raises(ValidationError) as excinfo:
        base_event(page="")
    check_error(excinfo, "The event page field is not None")
    with pytest.raises(ValidationError) as excinfo:
        base_event(page="None")
    check_error(excinfo, "The event page field is not None")
    with pytest.raises(ValidationError) as excinfo:
        base_event(page={})
    check_error(excinfo, "Not a valid string.")


def test_valid_referer_should_not_raise_exception(base_event):
    """Test that a valid referer does not raise a ValidationError"""
    try:
        base_event(referer="")
        base_event(referer="https://www.fun-mooc.fr/")
        base_event(
            referer=(
                "https://www.fun-mooc.fr/event?event_type=page_close&event=&page=https%3A%2F%2Fwww"
                ".fun-mooc.fr%2Fcourses%2Fcourse-v1%3Aulb%2B44013%2Bsession03%2Fcourseware%2Fdffbd"
                "36f242f44c2b8bcb83ba4aa4eba%2F71b51ecbeaa4492d9bad9e6ecba3e1cf%2F"
            ),
        )
    except ValidationError:
        pytest.fail("Valid base event ip address should not raise exceptions")


def test_invalid_referer_should_raise_exception(base_event):
    """Test that a invalid referer raise a ValidationError"""
    with pytest.raises(ValidationError) as excinfo:
        base_event(referer=1)
    check_error(excinfo, "Not a valid string.")
    with pytest.raises(ValidationError) as excinfo:
        base_event(referer="this/is/not/a/valid/relative/url")
    check_error(excinfo, "Not a valid URL.")


def test_valid_context_user_id_should_not_raise_exception(base_event):
    """Test that a valid context.user_id does not raise a ValidationError"""
    try:
        context = base_event(context_args={"user_id": ""}).iloc[0]["context"]
        assert context["user_id"] == ""
        context = base_event(context_args={"user_id": None}).iloc[0]["context"]
        assert context["user_id"] is None
        context = base_event(context_args={"user_id": 213456}).iloc[0]["context"]
        assert context["user_id"] == 213456
    except ValidationError:
        pytest.fail("Valid base event context.user_id should not raise exceptions")


def test_invalid_context_user_id_should_raise_exception(base_event):
    """Test that a invalid context.user_id raise a ValidationError"""
    with pytest.raises(ValidationError) as excinfo:
        base_event(context_args={"user_id": "invalid_user_id"})
    check_error(excinfo, "user_id should be None or an empty string or an Integer")
    with pytest.raises(ValidationError) as excinfo:
        base_event(context_args={"user_id": {}})
    check_error(excinfo, "user_id should be None or an empty string or an Integer")


def test_valid_context_org_id_and_course_id_should_not_raise_exception(base_event):
    """Test that a valid context.org_id and context.course_id does not raise a ValidationError"""
    context = base_event().iloc[0]["context"]
    try:
        context = base_event(context_args={"org_id": "", "course_id": ""}).iloc[0][
            "context"
        ]
        assert context["org_id"] == ""
        assert context["course_id"] == ""
        context = base_event(
            context_args={
                "org_id": "valid_org_id",
                "course_id": "course-v1:valid_org_id+valid_course_id+not_empty",
            },
        ).iloc[0]["context"]
        assert context["org_id"] == "valid_org_id"
        assert (
            context["course_id"] == "course-v1:valid_org_id+valid_course_id+not_empty"
        )
    except ValidationError:
        pytest.fail("Valid base event context.user_id should not raise exceptions")


def test_invalid_context_org_id_and_course_id_should_raise_exception(base_event):
    """Test that a invalid context.org_id and context.course_id raise a ValidationError"""
    context = {"org_id": 123, "course_id": "course-v1:123+valid_course_id+not_empty"}
    with pytest.raises(ValidationError) as excinfo:
        base_event(context_args=context)
    check_error(excinfo, "Not a valid string.")
    with pytest.raises(ValidationError) as excinfo:
        context["org_id"] = None
        context["course_id"] = "course-v1:+valid_course_id+not_empty"
        base_event(context_args=context)
    check_error(excinfo, "Field may not be null.")
    with pytest.raises(ValidationError) as excinfo:
        context["org_id"] = {}
        base_event(context_args=context)
    check_error(excinfo, "Not a valid string.")
    with pytest.raises(ValidationError) as excinfo:
        context["org_id"] = ""
        base_event(context_args=context)
    check_error(excinfo, "course_id should be empty if org_id is empty")
    with pytest.raises(ValidationError) as excinfo:
        context["org_id"] = "not_empty"
        base_event(context_args=context)
    check_error(
        excinfo, "organization ID in the course ID does not match", operator.contains
    )
    with pytest.raises(ValidationError) as excinfo:
        context["org_id"] = "org_id"
        context["course_id"] = "course-v1:NOT_org_id+invalid_course_id+not_empty"
        base_event(context_args=context)
    check_error(
        excinfo, "organization ID in the course ID does not match", operator.contains
    )
    with pytest.raises(ValidationError) as excinfo:
        context["course_id"] = "course-v1:org_id"
        base_event(context_args=context)
    check_error(
        excinfo,
        "course_id should contain an organization ID, a course name and session separated by a +",
    )
    with pytest.raises(ValidationError) as excinfo:
        context["course_id"] = "course-v1:org_id+missing_session_and_plus"
        base_event(context_args=context)
    check_error(
        excinfo,
        "course_id should contain an organization ID, a course name and session separated by a +",
    )
    with pytest.raises(ValidationError) as excinfo:
        context["course_id"] = "course-v1:org_id+missing_session+"
        base_event(context_args=context)
    check_error(excinfo, "course and session should not be empty")


def test_context_course_user_tags_should_be_missing_sometimes():
    """Test that the context.course_user_tags is sometimes not present
    and when it's not present the context.user_id is empty or None
    """

    def check_context_course_user_tags(context):
        """Check that when context_course_user_tags is missing the org_id is empty"""
        if "course_user_tags" not in context:
            assert context["org_id"] == ""
            return False
        return True

    is_course_user_tags_present = BULK_EVENTS["context"].apply(
        check_context_course_user_tags
    )
    assert is_course_user_tags_present.any() and not is_course_user_tags_present.all()


def test_event_fields_values_should_be_diverse():
    """Test that the event fields have diverse values"""
    non_unique_fields = ["ip", "agent", "host", "referer", "accept_language", "time"]
    assert (BULK_EVENTS[non_unique_fields].nunique() > 5).all()
    context = BULK_EVENTS["context"].apply(pd.Series)
    assert (context[["user_id", "org_id", "course_id", "path"]].nunique() > 5).all()
