"""
Tests for the base event schema
"""

# pylint: disable=redefined-outer-name
import operator

import pytest
from marshmallow import ValidationError
from marshmallow.fields import Nested

from ralph.schemas.edx.base import BaseEventSchema, ContextSchema

from tests.fixtures.logs import EventType, event_generator

from .test_common import check_error


@pytest.fixture()
def base_event():
    """Return a base event generator that generates size number of events"""

    return lambda **kwargs: event_generator(EventType.BASE_EVENT, **kwargs)


class BaseEventSchemaWithContext(BaseEventSchema):
    """A schema containing ContextSchema to test"""

    context = Nested(ContextSchema())


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
    assert event["event_source"] == "server"
    with pytest.raises(ValidationError) as excinfo:
        base_event(event_source="not_server")
    check_error(excinfo, "The event event_source field is not `server`")


def test_page_should_be_none(base_event):
    """Test that the page is equal to `None` and if not the
    event is invalid and should rais a ValidationError
    """

    event = base_event()
    assert event["page"] is None
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
        context = base_event(context_args={"user_id": ""})["context"]
        assert context["user_id"] == ""
        context = base_event(context_args={"user_id": None})["context"]
        assert context["user_id"] is None
        context = base_event(context_args={"user_id": 213456})["context"]
        assert context["user_id"] == 213456
    except ValidationError:
        pytest.fail("Valid base event context.user_id should not raise exceptions")


def test_invalid_context_user_id_should_raise_exception(base_event):
    """Test that a invalid context.user_id raise a ValidationError"""

    with pytest.raises(ValidationError) as excinfo:
        base_event(context_args={"user_id": "invalid_user_id"})
    check_error(excinfo, "user_id should be None, an empty string or an integer")
    with pytest.raises(ValidationError) as excinfo:
        base_event(context_args={"user_id": {}})
    check_error(excinfo, "user_id should be None, an empty string or an integer")


def test_valid_context_org_id_and_course_id_should_not_raise_exception(base_event):
    """Test that a valid context.org_id and context.course_id does not raise a ValidationError"""

    context = base_event()["context"]
    try:
        context = base_event(context_args={"org_id": "", "course_id": ""})["context"]
        assert context["org_id"] == ""
        assert context["course_id"] == ""
        context = base_event(
            context_args={
                "org_id": "valid_org_id",
                "course_id": "course-v1:valid_org_id+valid_course_id+not_empty",
            },
        )["context"]
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
        context["course_id"] = ""
        base_event(context_args=context)
    check_error(excinfo, "org_id should be empty if course_id is empty")
    with pytest.raises(ValidationError) as excinfo:
        context["course_id"] = "+missing_course-v1+not_empty"
        base_event(context_args=context)
    check_error(excinfo, "course_id should starts with 'course-v1'")
    with pytest.raises(ValidationError) as excinfo:
        context["course_id"] = "course-v1:+valid_course_id+not_empty"
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


def test_valid_context_path_should_not_raise_exception(base_event):
    """Test that a valid context.org_id and context.course_id does not raise a ValidationError"""

    event = base_event(
        context_args={
            "course_id": "course-v1:organisationCourse+numeroCours+sessiondCours",
            "org_id": "organisationCourse",
            "path": (
                "/courses/course-v1:organisationCourse+numeroCours+sessiondCours/xblock/"
                "block-v1:organisationCourse+numeroCours+sessiondCours+type@problem+block@"
                "cc2a00e69f7a4dd8b560f4e48911206f/handler/"
            ),
        }
    )
    event["context"]["module"] = {
        "usage_key": (
            "block-v1:organisationCourse+numeroCours+sessiondCours+type@problem+block@"
            "cc2a00e69f7a4dd8b560f4e48911206f"
        ),
        "display_name": "any display name",
    }
    try:
        BaseEventSchemaWithContext().load(event)
    except ValidationError:
        pytest.fail(
            "Valid base event with context containing module should not raise exceptions"
        )


def test_invalid_context_path_should_raise_exception(base_event):
    """Test that a invalid context.path raise a ValidationError"""

    event = base_event(
        context_args={
            "course_id": "course-v1:organisationCourse+numeroCours+sessiondCours",
            "org_id": "organisationCourse",
            "path": "/does/not/contain/the/module/usage_key",
        }
    )
    event["context"]["module"] = {
        "usage_key": (
            "block-v1:organisationCourse+numeroCours+sessiondCours+type@problem+block@"
            "cc2a00e69f7a4dd8b560f4e48911206f"
        ),
        "display_name": "any display name",
    }
    with pytest.raises(ValidationError) as excinfo:
        BaseEventSchemaWithContext().load(event)
    check_error(
        excinfo,
        (
            "path should start with: "
            "/courses/course-v1:organisationCourse+numeroCours+sessiondCours/xblock/"
            "block-v1:organisationCourse+numeroCours+sessiondCours+type@problem+block@"
            "cc2a00e69f7a4dd8b560f4e48911206f/handler/"
        ),
        operator_type=operator.contains,
    )


def test_get_course_key(base_event):
    """Test that static function get_course_key returns the course_key of the event"""

    event = base_event(
        context_args={
            "course_id": "course-v1:organisationCourse+numeroCours+sessiondCours",
            "org_id": "organisationCourse",
        }
    )
    assert (
        BaseEventSchema.get_course_key(event)
        == "organisationCourse+numeroCours+sessiondCours"
    )


def test_get_block_id(base_event):
    """Test that static function get_block_id returns the block_id from the event"""

    event = base_event(
        context_args={
            "course_id": "course-v1:organisationCourse+numeroCours+sessiondCours",
            "org_id": "organisationCourse",
        }
    )
    assert BaseEventSchema.get_block_id(event) == (
        "block-v1:organisationCourse+numeroCours+sessiondCours+type@problem+block@"
    )
