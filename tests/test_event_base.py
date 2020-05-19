"""
Tests for the FeedbackDisplayed event schema
"""
# pylint: disable=redefined-outer-name
import pandas as pd
import pytest
from marshmallow import ValidationError

from .fixtures.logs import EventType, _event

BULK_EVENTS = _event(50, EventType.BASEEVENT)


@pytest.fixture()
def base_events():
    """Returns a base event generator that generates size number of events"""
    return lambda size, **kwargs: _event(size, EventType.BASEEVENT, **kwargs)


def test_valid_ip_should_not_raise_exception(base_events):
    """Test that a valid ip address does not raise a ValidationError"""
    try:
        base_events(1, ip="51.255.9.27")
        base_events(1, ip="8.8.8.8")
        base_events(1, ip="")
    except ValidationError:
        pytest.fail("Valid base event ip address should not raise exceptions")


def test_invalid_ip_should_raise_exception(base_events):
    """Test that a invalid ip addresse raise ValidationError"""
    with pytest.raises(ValidationError):
        base_events(1, ip="invalid_ip")
    with pytest.raises(ValidationError):
        base_events(1, ip="  ")
    with pytest.raises(ValidationError):
        base_events(1, ip="051.255.9.27")


def test_empty_fields_should_not_raise_exception(base_events):
    """Test that an empty agent / host / referer / accept_language
    does not raise ValidationError
    """
    try:
        base_events(1, agent="")
        base_events(1, host="")
        base_events(1, referer="")
    except ValidationError:
        pytest.fail("Valid base event agent field should not raise exceptions")


def test_event_source_should_be_server(base_events):
    """Test that the event_source is equal to `server` and if not the
    event is invalid and should raise a ValidationException
    """
    event = base_events(1)
    assert event.iloc[0]["event_source"] == "server"
    with pytest.raises(ValidationError):
        base_events(1, event_source="not_server")


def test_page_should_be_none(base_events):
    """Test that the page is equal to `None` and if not the
    event is invalid and should rais a ValidationError
    """
    event = base_events(1)
    assert event.iloc[0]["page"] is None
    with pytest.raises(ValidationError):
        base_events(1, page="not_None")
    with pytest.raises(ValidationError):
        base_events(1, page=0)
    with pytest.raises(ValidationError):
        base_events(1, page="")
    with pytest.raises(ValidationError):
        base_events(1, page={})


def test_valid_referer_should_not_raise_exception(base_events):
    """Test that a valid referer does not raise a ValidationError"""
    try:
        base_events(1, referer="")
        base_events(1, referer="https://www.fun-mooc.fr/")
        base_events(
            1,
            referer=(
                "https://www.fun-mooc.fr/event?event_type=page_close&event=&page=https%3A%2F%2Fwww"
                ".fun-mooc.fr%2Fcourses%2Fcourse-v1%3Aulb%2B44013%2Bsession03%2Fcourseware%2Fdffbd"
                "36f242f44c2b8bcb83ba4aa4eba%2F71b51ecbeaa4492d9bad9e6ecba3e1cf%2F"
            ),
        )
    except ValidationError:
        pytest.fail("Valid base event ip address should not raise exceptions")


def test_invalid_referer_should_raise_exception(base_events):
    """Test that a invalid referer raise a ValidationError"""
    with pytest.raises(ValidationError):
        base_events(1, referer=1)
    with pytest.raises(ValidationError):
        base_events(1, referer="this/is/not/a/valid/relative/url")


def test_valid_context_user_id_should_not_raise_exception(base_events):
    """Test that a valid context.user_id does not raise a ValidationError"""
    try:
        context = base_events(1, context_args={"user_id": ""}).iloc[0]["context"]
        assert context["user_id"] == ""
        context = base_events(1, context_args={"user_id": None}).iloc[0]["context"]
        assert context["user_id"] is None
        context = base_events(1, context_args={"user_id": 213456}).iloc[0]["context"]
        assert context["user_id"] == 213456
    except ValidationError:
        pytest.fail("Valid base event context.user_id should not raise exceptions")


def test_invalid_context_user_id_should_raise_exception(base_events):
    """Test that a invalid context.user_id raise a ValidationError"""
    with pytest.raises(ValidationError):
        base_events(1, context_args={"user_id": "invalid_user_id"})
    with pytest.raises(ValidationError):
        base_events(1, context_args={"user_id": {}})


def test_valid_context_org_id_and_course_id_should_not_raise_exception(base_events):
    """Test that a valid context.org_id and context.course_id does not raise a ValidationError"""
    context = base_events(1).iloc[0]["context"]
    try:
        context = base_events(1, context_args={"org_id": "", "course_id": ""}).iloc[0][
            "context"
        ]
        assert context["org_id"] == ""
        assert context["course_id"] == ""
        context = base_events(
            1,
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


def test_invalid_context_org_id_and_course_id_should_raise_exception(base_events):
    """Test that a invalid context.org_id and context.course_id raise a ValidationError"""
    context = {"org_id": 123, "course_id": "course-v1:123+valid_course_id+not_empty"}
    with pytest.raises(ValidationError):
        base_events(1, context_args=context)
    with pytest.raises(ValidationError):
        context["org_id"] = None
        context["course_id"] = "course-v1:+valid_course_id+not_empty"
        base_events(1, context_args=context)
    with pytest.raises(ValidationError):
        context["org_id"] = {}
        base_events(1, context_args=context)
    with pytest.raises(ValidationError):
        context["org_id"] = ""
        base_events(1, context_args=context)
    with pytest.raises(ValidationError):
        context["org_id"] = "not_empty"
        base_events(1, context_args=context)
    with pytest.raises(ValidationError):
        context["org_id"] = "org_id"
        context["course_id"] = "course-v1:NOT_org_id+invalid_course_id+not_empty"
        base_events(1, context_args=context)
    with pytest.raises(ValidationError):
        context["course_id"] = "course-v1:org_id"
        base_events(1, context_args=context)
    with pytest.raises(ValidationError):
        context["course_id"] = "course-v1:org_id+missing_session_and_plus"
        base_events(1, context_args=context)
    with pytest.raises(ValidationError):
        context["course_id"] = "course-v1:org_id+missing_session+"
        base_events(1, context_args=context)


def check_context_course_user_tags(context):
    """Check that when context_course_user_tags is missing the org_id is empty"""
    if "course_user_tags" not in context:
        assert context["org_id"] == ""
        return False
    return True


def test_context_course_user_tags_should_be_missing_sometimes():
    """Test that the context.course_user_tags is sometimes not present
    and when it's not present the context.user_id is empty or None
    """
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
