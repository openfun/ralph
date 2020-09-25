"""
Tests for the Browser event schema
"""
# pylint: disable=redefined-outer-name
import json
import operator
import urllib.parse

import pytest
from marshmallow import ValidationError

from ralph.schemas.edx.browser import (
    BROWSER_EVENT_TYPE_FIELD,
    BROWSER_NAME_FIELD,
    BaseBrowserEventSchema,
)

from tests.fixtures.logs import EventType, _event

from .test_common import check_error, check_loading_valid_events

ORG_ID = "org"
COURSE_ID = "course-v1:org+course+session"
MD5 = "9cc0b13998d74e6ca57b5aa77718b97b"


@pytest.fixture()
def base_browser_event():
    """Returns a base browser event generator that generates size number of events"""
    return lambda size=1, **kwargs: _event(size, EventType.BROWSER_BASE, **kwargs)


@pytest.fixture()
def page_close_event():
    """Returns a page_close browser event generator that generates size number of events"""
    return lambda size=1, **kwargs: _event(size, EventType.BROWSER_PAGE_CLOSE, **kwargs)


@pytest.fixture()
def problem_check_event():
    """Returns a page_close browser event generator that generates size number of events"""
    return lambda size=1, **kwargs: _event(
        size, EventType.BROWSER_PROBLEM_CHECK, **kwargs
    )


@pytest.fixture()
def default_browser_event():
    """Generates one browser event with default org_id and course_id
    given the event_type enum
    """

    def _default_browser_event(event_type, **kwargs):
        return _event(
            1,
            event_type,
            context_args={"org_id": ORG_ID, "course_id": COURSE_ID},
            **kwargs,
        )

    return _default_browser_event


def test_loading_valid_events_should_not_raise_exceptions():
    """Test that loading valid events does not raise exceptions"""
    check_loading_valid_events(BaseBrowserEventSchema(), "browser_event")


def test_valid_event_source_should_not_raise_exception(base_browser_event):
    """Test that a valid event_source not raise a ValidationError"""
    try:
        base_browser_event()
        base_browser_event(event_source="browser")
    except ValidationError:
        pytest.fail("Valid browser event event_source should not raise exceptions")


def test_invalid_event_source_should_raise_exception(base_browser_event):
    """Test that a invalid event_source raise ValidationError"""
    with pytest.raises(ValidationError) as excinfo:
        base_browser_event(event_source="not_browser")
    check_error(excinfo, "The event event_source field is not `browser`")


def test_valid_session_should_not_raise_exception(base_browser_event):
    """Test that a valid session does not raise a ValidationError"""
    try:
        base_browser_event(session="")
        base_browser_event(session="The_session_is_32_character_long")
    except ValidationError:
        pytest.fail("Valid browser event session should not raise exceptions")


def test_invalid_session_should_raise_exception(base_browser_event):
    """Test that a invalid session raise ValidationError"""
    with pytest.raises(ValidationError) as excinfo:
        base_browser_event(session="less_than_32_charactees")
    check_error(excinfo, "Session should be empty or 32 chars long (MD5)")
    with pytest.raises(ValidationError) as excinfo:
        base_browser_event(session="The_session_is_more_than_32_character_long")
    check_error(excinfo, "Session should be empty or 32 chars long (MD5)")
    with pytest.raises(ValidationError) as excinfo:
        base_browser_event(session=None)
    check_error(excinfo, "Field may not be null.")


def test_valid_page_should_not_raise_exception(base_browser_event):
    """Test that a valid page does not raise a ValidationError"""
    try:
        base_browser_event(page="https://www.fun-mooc.fr/")
        base_browser_event(page="/this/is/a/valid/relative/url")
        base_browser_event(page="/")
    except ValidationError:
        pytest.fail("Valid browser event page should not raise exceptions")


def test_invalid_page_should_raise_exception(base_browser_event):
    """Test that a invalid page raise ValidationError"""
    with pytest.raises(ValidationError) as excinfo:
        base_browser_event(page="invalid/url")
    check_error(excinfo, "Not a valid URL.")

    with pytest.raises(ValidationError) as excinfo:
        base_browser_event(page="")
    check_error(excinfo, "Not a valid URL.")

    with pytest.raises(ValidationError) as excinfo:
        base_browser_event(page=None)
    check_error(excinfo, "Field may not be null.")


def test_valid_event_type_and_name_should_not_raise_exception(base_browser_event):
    """Test that a valid event_type does not raise a ValidationError"""
    try:
        for event_type in BROWSER_EVENT_TYPE_FIELD:
            event = base_browser_event(event_type=event_type).iloc[0]
            if event_type != "book":
                assert event["event_type"] == event["name"]
            else:
                assert event["name"] in BROWSER_NAME_FIELD
    except ValidationError:
        pytest.fail("Valid browser event_type should not raise exceptions")


def test_invalid_event_type_and_name_should_raise_exception(base_browser_event):
    """Test that a invalid event_type_and_name raise ValidationError"""
    with pytest.raises(ValidationError) as excinfo:
        base_browser_event(event_type="not_in_BROWSER_EVENT_TYPE_FIELD")
    check_error(excinfo, "The event name field value is not one of the valid values")

    with pytest.raises(ValidationError) as excinfo:
        base_browser_event(event_type="page_close", name="not_page_close")
    check_error(
        excinfo,
        "The name field should be equal to the event_type when event_type is not `book`",
    )

    with pytest.raises(ValidationError) as excinfo:
        base_browser_event(event_type="page_close", name="problem_show")
    check_error(
        excinfo,
        "The name field should be equal to the event_type when event_type is not `book`",
    )

    with pytest.raises(ValidationError) as excinfo:
        base_browser_event(event_type="book", name="book")
    check_error(excinfo, "The name field is not one of the allowed values")


def test_valid_event_with_event_type_page_close(page_close_event):
    """Test that a valid event value does not raise a ValidationError"""
    try:
        page_close_event(event="{}")
    except ValidationError:
        pytest.fail("Valid browser event_type `page_close` should not raise exceptions")


def test_invalid_event_type_page_close(page_close_event):
    """Test that a invalid event value raise a ValidationError"""
    with pytest.raises(ValidationError) as excinfo:
        page_close_event(event='{"key": "value"}')
    check_error(excinfo, "Event should be an empty JSON")

    with pytest.raises(ValidationError) as excinfo:
        page_close_event(event="")
    check_error(excinfo, "Event should be an empty JSON")


def test_valid_event_with_event_type_problem_show(default_browser_event):
    """Test that a valid event value does not raise a ValidationError"""
    problem = f"block-v1:{COURSE_ID[10:]}+type@problem+block@{MD5}"
    try:
        event = json.dumps({"problem": problem})
        default_browser_event(event_type=EventType.BROWSER_PROBLEM_SHOW, event=event)
    except ValidationError:
        pytest.fail(
            "Valid browser event_type `problem_show` should not raise exceptions"
        )


def test_invalid_event_type_problem_show(default_browser_event):
    """Test that a invalid event value raise a ValidationError"""
    problem = f"block-v1:NOTorg+course+session+type@problem+block@{MD5}"
    with pytest.raises(ValidationError) as excinfo:
        event = json.dumps({"problem": problem})
        default_browser_event(event_type=EventType.BROWSER_PROBLEM_SHOW, event=event)
    check_error(
        excinfo,
        "Event problem should start with `block-v1:org+course+session+type@problem+block@`",
        operator.contains,
    )

    with pytest.raises(ValidationError) as excinfo:
        problem = f"block-v1:{COURSE_ID[10:]}+type@problem+block@{MD5}"
        event = json.dumps({"NOTproblem": problem})
        default_browser_event(event_type=EventType.BROWSER_PROBLEM_SHOW, event=event)
    check_error(
        excinfo,
        "{'problem'} key is required for event, {'NOTproblem'} key is not valid for event",
    )

    with pytest.raises(ValidationError) as excinfo:
        default_browser_event(event_type=EventType.BROWSER_PROBLEM_SHOW, event="{}")
    check_error(excinfo, "{'problem'} key is required for event", operator.contains)


def test_valid_event_type_problem_check(problem_check_event):
    """Test that a valid event value does not raise a ValidationError"""
    event = problem_check_event().iloc[0]["event"]
    assert isinstance(event, str)
    assert len(urllib.parse.parse_qs(event)) >= 1 or event == ""
    try:
        event = ""
        problem_check_event(event=event)
        event = "input_2394233ce59042f6ae67339dd4629fd8_2_1=Spain"
        problem_check_event(event=event)
        event = "input_cc2a00e69f7a4dd8b560f4e48911206f_2_1="
        problem_check_event(event=event)
        event = (
            "input_cc2a00e69f7a4dd8b560f4e48911206f_2_1=&"
            "input_cc2a00e69f7a4dd8b560f4e48911206f_3_1="
        )
        problem_check_event(event=event)
        event = (
            "input_0924f1350d02437da3c4451e1582acd1_2_1%5B%5D=choice_0&"
            "input_0924f1350d02437da3c4451e1582acd1_2_1%5B%5D=choice_1&"
            "input_0924f1350d02437da3c4451e1582acd1_2_1%5B%5D=choice_3&"
            "input_0924f1350d02437da3c4451e1582acd1_3_1%5B%5D=choice_0&"
            "input_0924f1350d02437da3c4451e1582acd1_3_1%5B%5D=choice_1&"
            "input_0924f1350d02437da3c4451e1582acd1_3_1%5B%5D=choice_3"
        )
        problem_check_event(event=event)
    except ValidationError:
        pytest.fail(
            "Valid browser event_type `problem_check` should not raise exceptions"
        )


def test_invalid_event_type_problem_check(problem_check_event):
    """Test that a invalid problem_check browser event does raise a ValidationError"""
    with pytest.raises(ValidationError) as excinfo:
        problem_check_event(event="{}")
    check_error(excinfo, "Event should be a valid URL-encoded string")
    with pytest.raises(ValidationError) as excinfo:
        problem_check_event(event="invalid URL-encoded string")
    check_error(excinfo, "Event should be a valid URL-encoded string")
    with pytest.raises(ValidationError) as excinfo:
        problem_check_event(event=None)
    check_error(excinfo, "Field may not be null.")
    with pytest.raises(ValidationError) as excinfo:
        problem_check_event(event=123)
    check_error(excinfo, "Event should be a valid URL-encoded string")


def test_valid_event_type_problem_graded_or_similar(event):
    """Test that a valid event value does not raise a ValidationError
    for browser events: problem_graded, problem_reset and problem_save
    """
    try:
        for event_type in [
            EventType.BROWSER_PROBLEM_GRADED,
            EventType.BROWSER_PROBLEM_RESET,
            EventType.BROWSER_PROBLEM_SAVE,
        ]:
            event_field = [
                "input_d9fd0115d0be4fe08281f2eaf361744c_2_1=Spain",
                "any string",
            ]
            event(1, event_type, event=event_field)
            event_field = [
                (
                    "input_afa254601f4b48128baf1c3e7054fb59_2_1=1%5E6&"
                    "input_afa254601f4b48128baf1c3e7054fb59_3_1=10"
                ),
                "any string",
            ]
            event(1, event_type, event=event_field)
    except ValidationError:
        pytest.fail(f"Valid `{event_type.name}` event should not raise exceptions")


def test_invalid_event_type_problem_graded_or_similar(event):
    """Test that a invalid problem_graded problem_reset and
    problem_save browser event does raise a ValidationError """
    for event_type in [
        EventType.BROWSER_PROBLEM_GRADED,
        EventType.BROWSER_PROBLEM_RESET,
        EventType.BROWSER_PROBLEM_SAVE,
    ]:
        with pytest.raises(ValidationError) as excinfo:
            event(1, event_type, event=[])
        check_error(excinfo, "Event should be a two-items list")
        with pytest.raises(ValidationError) as excinfo:
            event(
                1,
                event_type,
                event=["input_d9fd0115d0be4fe08281f2eaf361744c_2_1=Spain"],
            )
        check_error(excinfo, "Event should be a two-items list")
        with pytest.raises(ValidationError) as excinfo:
            event(
                1,
                event_type,
                event=[
                    "input_d9fd0115d0be4fe08281f2eaf361744c_2_1=Spain",
                    "foo",
                    "bar",
                ],
            )
        check_error(excinfo, "Event should be a two-items list")
        with pytest.raises(ValidationError) as excinfo:
            event(
                1,
                event_type,
                event=["input_d9fd0115d0be4fe08281f2eaf361744c_2_1", "any_string"],
            )
        check_error(
            excinfo, "Event list first item should be a valid URL-encoded string"
        )


def test_valid_event_type_seq_goto(default_browser_event):
    """Test that a valid event value does not raise a ValidationError"""
    id_value = f"block-v1:{COURSE_ID[10:]}+type@sequential+block@{MD5}"
    event = json.dumps({"new": 1, "old": 1, "id": id_value})
    try:
        default_browser_event(EventType.BROWSER_SEQ_GOTO, event=event)
    except ValidationError:
        pytest.fail("Valid browser event_type `seq_goto` should not raise exceptions")


def test_invalid_event_type_seq_goto_with_unparsable_json(default_browser_event):
    """Test that a invalid seq_goto browser event does raise a ValidationError"""
    with pytest.raises(ValidationError) as excinfo:
        default_browser_event(EventType.BROWSER_SEQ_GOTO, event="")
    check_error(excinfo, "Event should contain a parsable JSON string")

    with pytest.raises(ValidationError) as excinfo:
        default_browser_event(EventType.BROWSER_SEQ_GOTO, event={"new": 1})
    check_error(excinfo, "Event should contain a parsable JSON string")


def test_invalid_event_type_seq_goto_with_invalid_key_values(default_browser_event):
    """Test that a invalid seq_goto browser event does raise a ValidationError"""
    id_value = f"block-v1:{COURSE_ID[10:]}+type@sequential+block@{MD5}"
    event = {"new": "not a number", "old": 1, "id": id_value}
    with pytest.raises(ValidationError) as excinfo:
        default_browser_event(EventType.BROWSER_SEQ_GOTO, event=json.dumps(event))
    check_error(excinfo, "Event new and old fields should be integers")

    event["new"] = 1
    event["id"] = f"block-v1:invalid+course+key+type@sequential+block@{MD5}"
    with pytest.raises(ValidationError) as excinfo:
        default_browser_event(EventType.BROWSER_SEQ_GOTO, event=json.dumps(event))
    check_error(excinfo, "The id should start with block-v1:org", operator.contains)

    event["id"] = f"block-v1:{COURSE_ID[10:]}+type@sequential+block@invalid_id"
    with pytest.raises(ValidationError) as excinfo:
        default_browser_event(EventType.BROWSER_SEQ_GOTO, event=json.dumps(event))
    check_error(excinfo, "The id should end with a 32 long MD5 hash")


def test_invalid_event_type_seq_goto_with_missing_or_additional_keys(
    default_browser_event,
):
    """Test that a invalid seq_goto browser event does raise a ValidationError"""
    id_value = f"block-v1:{COURSE_ID[10:]}+type@sequential+block@{MD5}"
    event = {"old": 1, "id": id_value}
    with pytest.raises(ValidationError) as excinfo:
        default_browser_event(EventType.BROWSER_SEQ_GOTO, event=json.dumps(event))
    check_error(excinfo, "{'new'} key is required for event", operator.contains)

    event["new"] = 1
    del event["old"]
    with pytest.raises(ValidationError) as excinfo:
        default_browser_event(EventType.BROWSER_SEQ_GOTO, event=json.dumps(event))
    check_error(excinfo, "{'old'} key is required for event", operator.contains)

    event["old"] = 1
    del event["id"]
    with pytest.raises(ValidationError) as excinfo:
        default_browser_event(EventType.BROWSER_SEQ_GOTO, event=json.dumps(event))
    check_error(excinfo, "{'id'} key is required for event", operator.contains)
    event["id"] = id_value
    event["invalid_key"] = "invalid_value"
    with pytest.raises(ValidationError) as excinfo:
        default_browser_event(EventType.BROWSER_SEQ_GOTO, event=json.dumps(event))
    check_error(excinfo, "{'invalid_key'} key is not valid", operator.contains)


def test_valid_event_type_seq_next_and_seq_prev(default_browser_event):
    """Test that a valid event value does not raise a ValidationError"""
    try:
        for event_type in [EventType.BROWSER_SEQ_NEXT, EventType.BROWSER_SEQ_PREV]:
            new = 3 if event_type == EventType.BROWSER_SEQ_NEXT else 1
            id_value = f"block-v1:{COURSE_ID[10:]}+type@sequential+block@{MD5}"
            event = json.dumps({"new": new, "old": 2, "id": id_value})
            default_browser_event(event_type, event=event)
    except ValidationError:
        pytest.fail(
            f"Valid browser event_type `{event_type.name}`should not raise exceptions"
        )


def test_invalid_event_type_seq_next_and_seq_prev(default_browser_event):
    """Test that a invalid event value raise a ValidationError"""
    event = {"id": (f"block-v1:{COURSE_ID[10:]}+type@sequential+block@{MD5}")}

    with pytest.raises(ValidationError) as excinfo:
        event["new"] = 1
        event["old"] = 1
        default_browser_event(EventType.BROWSER_SEQ_NEXT, event=json.dumps(event))
    check_error(excinfo, "Event new field (1) should be equal to old (1) + 1")

    with pytest.raises(ValidationError) as excinfo:
        default_browser_event(EventType.BROWSER_SEQ_PREV, event=json.dumps(event))
    check_error(excinfo, "Event new field (1) should be equal to old (1) - 1")

    with pytest.raises(ValidationError) as excinfo:
        event["new"] = 1
        event["old"] = 2
        default_browser_event(EventType.BROWSER_SEQ_NEXT, event=json.dumps(event))
    check_error(excinfo, "Event new field (1) should be equal to old (2) + 1")

    with pytest.raises(ValidationError) as excinfo:
        event["new"] = 2
        event["old"] = 1
        default_browser_event(EventType.BROWSER_SEQ_PREV, event=json.dumps(event))
    check_error(excinfo, "Event new field (2) should be equal to old (1) - 1")

    with pytest.raises(ValidationError) as excinfo:
        event["new"] = 3
        event["old"] = 1
        default_browser_event(EventType.BROWSER_SEQ_PREV, event=json.dumps(event))
    check_error(excinfo, "Event new field (3) should be equal to old (1) - 1")

    with pytest.raises(ValidationError) as excinfo:
        event["new"] = 1
        event["old"] = 3
        default_browser_event(EventType.BROWSER_SEQ_PREV, event=json.dumps(event))
    check_error(excinfo, "Event new field (1) should be equal to old (3) - 1")


def test_valid_event_type_textbook_pdf_thumbnail_outline_toggled(default_browser_event):
    """Test that a valid event value does not raise a ValidationError
    for browser events: textbook.pdf.thumbnails.toggled,
    textbook.pdf.outline.toggled and textbook.pdf.page.navigated
    """
    event = {
        "chapter": f"/asset-v1:{COURSE_ID[10:]}+type@asset+block/test.pdf",
        "page": 1,
    }
    try:
        for event_type in [
            EventType.BROWSER_TEXTBOOK_PDF_THUMBNAILS_TOGGLED,
            EventType.BROWSER_TEXTBOOK_PDF_OUTLINE_TOGGLED,
            EventType.BROWSER_TEXTBOOK_PDF_PAGE_NAVIGATED,
        ]:
            event["name"] = event_type.name.lower()[8:].replace("_", ".")
            default_browser_event(event_type, event=json.dumps(event))
    except ValidationError:
        pytest.fail(
            f"Valid browser event_type `{event_type.name}`should not raise exceptions"
        )


def test_invalid_event_type_textbook_pdf_thumbnail_outline_toggled(
    default_browser_event,
):
    """Test that a invalid event value does raise a ValidationError"""
    event = {}
    for event_type in [
        EventType.BROWSER_TEXTBOOK_PDF_THUMBNAILS_TOGGLED,
        EventType.BROWSER_TEXTBOOK_PDF_OUTLINE_TOGGLED,
        EventType.BROWSER_TEXTBOOK_PDF_PAGE_NAVIGATED,
    ]:
        with pytest.raises(ValidationError) as excinfo:
            event["name"] = event_type.name.lower()[8:].replace("_", ".")
            event["page"] = 1
            event["chapter"] = f"/asset-v1:{COURSE_ID[10:]}+type@asset+block/test.pdf"
            default_browser_event(event_type, event=event)
        check_error(excinfo, "Event should contain a parsable JSON string")

        check_invalid_thumbnail_outline_toggled_page(
            default_browser_event, event, event_type
        )
        check_invalid_thumbnail_outline_toggled_name(
            default_browser_event, event, event_type
        )
        check_invalid_thumbnail_outline_toggled_chapter(
            default_browser_event, event, event_type
        )


def check_invalid_thumbnail_outline_toggled_page(
    default_browser_event, event, event_type
):
    """check event page field for textbook.pdf.thumbnails.toggled,
    textbook.pdf.outline.toggled, textbook.pdf.page.navigated """
    with pytest.raises(ValidationError) as excinfo:
        del event["page"]
        default_browser_event(event_type, event=json.dumps(event))
    check_error(excinfo, "{'page'} key is required for event", operator.contains)

    with pytest.raises(ValidationError) as excinfo:
        event["page"] = "not_integer"
        default_browser_event(event_type, event=json.dumps(event))
    check_error(excinfo, "Event page should a positive integer")

    with pytest.raises(ValidationError) as excinfo:
        event["page"] = "123"
        default_browser_event(event_type, event=json.dumps(event))
    check_error(excinfo, "Event page should a positive integer")

    with pytest.raises(ValidationError) as excinfo:
        event["page"] = -1
        default_browser_event(event_type, event=json.dumps(event))
    check_error(excinfo, "Event page should a positive integer")


def check_invalid_thumbnail_outline_toggled_name(
    default_browser_event, event, event_type
):
    """check event name field for textbook.pdf.thumbnails.toggled,
    textbook.pdf.outline.toggled, textbook.pdf.page.navigated """
    with pytest.raises(ValidationError) as excinfo:
        event["page"] = 132
        del event["name"]
        default_browser_event(event_type, event=json.dumps(event))
    check_error(excinfo, "{'name'} key is required for event", operator.contains)

    with pytest.raises(ValidationError) as excinfo:
        event["name"] = "not_event_type"
        default_browser_event(event_type, event=json.dumps(event))
    check_error(excinfo, "Event name should be equal to the browser event name")

    with pytest.raises(ValidationError) as excinfo:
        event["name"] = event_type.name.lower()[8:].replace("_", ".")
        del event["chapter"]
        default_browser_event(event_type, event=json.dumps(event))
    check_error(excinfo, "{'chapter'} key is required for event", operator.contains)


def check_invalid_thumbnail_outline_toggled_chapter(
    default_browser_event, event, event_type
):
    """check event chapter field for textbook.pdf.thumbnails.toggled,
    textbook.pdf.outline.toggled, textbook.pdf.page.navigated """
    with pytest.raises(ValidationError) as excinfo:
        event["chapter"] = f"/asset-v1:{COURSE_ID[10:]}+type@asset+block/test.xml"
        default_browser_event(event_type, event=json.dumps(event))
    check_error(excinfo, "Event chapter should end with the .pdf extension")

    with pytest.raises(ValidationError) as excinfo:
        event["chapter"] = f"/asset-v1:{COURSE_ID[10:]}+type@not_asset+block/test.pdf"
        default_browser_event(event_type, event=json.dumps(event))
    check_error(
        excinfo,
        "Event chapter should begin with /asset-v1:org+course+session+type@asset+block/",
        operator.contains,
    )

    with pytest.raises(ValidationError) as excinfo:
        event["chapter"] = f"/asset-v1:invalid+course+key+type@asset+block/test.pdf"
        default_browser_event(event_type, event=json.dumps(event))
    check_error(
        excinfo,
        "Event chapter should begin with /asset-v1:org+course+session+type@asset+block/",
        operator.contains,
    )


def test_valid_event_type_textbook_pdf_thumbnail_navigated(default_browser_event):
    """Test that a valid event value does not raise a ValidationError
    for browser event type textbook.pdf.thumbnail.navigated
    """
    event = {
        "chapter": f"/asset-v1:{COURSE_ID[10:]}+type@asset+block/test.pdf",
        "page": 1,
        "name": "textbook.pdf.thumbnail.navigated",
        "thumbnail_title": "Page 1",
    }
    try:
        default_browser_event(
            EventType.BROWSER_TEXTBOOK_PDF_THUMBNAIL_NAVIGATED, event=json.dumps(event)
        )
    except ValidationError:
        pytest.fail(
            f"Valid browser event_type textbook.pdf.thumbnail.navigated"
            f"should not raise exceptions"
        )


def test_invalid_event_type_textbook_pdf_thumbnail_navigated(default_browser_event):
    """Test that a invalid event value does raise a ValidationError
    for browser events: textbook.pdf.thumbnail.navigated
    """
    event = {
        "chapter": f"/asset-v1:{COURSE_ID[10:]}+type@asset+block/test.pdf",
        "page": 1,
        "name": "textbook.pdf.thumbnail.navigated",
    }
    with pytest.raises(ValidationError) as excinfo:
        default_browser_event(
            EventType.BROWSER_TEXTBOOK_PDF_THUMBNAIL_NAVIGATED, event=json.dumps(event)
        )
    check_error(
        excinfo, "{'thumbnail_title'} key is required for event", operator.contains
    )
    with pytest.raises(ValidationError) as excinfo:
        event["thumbnail_title"] = 123
        default_browser_event(
            EventType.BROWSER_TEXTBOOK_PDF_THUMBNAIL_NAVIGATED, event=json.dumps(event)
        )
    check_error(excinfo, "thumbnail_title should be a string")


def test_valid_event_type_textbook_pdf_zoom_buttons_changed(default_browser_event):
    """Test that a valid event value does not raise a ValidationError
    for browser event type textbook.pdf.zoom.buttons.changed and
    textbook.pdf.page.scrolled
    """
    event = {
        "chapter": f"/asset-v1:{COURSE_ID[10:]}+type@asset+block/test.pdf",
        "page": 1,
    }
    try:
        for event_type in [
            EventType.BROWSER_TEXTBOOK_PDF_ZOOM_BUTTONS_CHANGED,
            EventType.BROWSER_TEXTBOOK_PDF_PAGE_SCROLLED,
        ]:
            event["name"] = event_type.name.lower()[8:].replace("_", ".")
            event["direction"] = "in" if event_type.name[-7:] == "CHANGED" else "up"
            default_browser_event(event_type, event=json.dumps(event))

            event["direction"] = "out" if event_type.name[-7:] == "CHANGED" else "down"
            default_browser_event(event_type, event=json.dumps(event))
    except ValidationError:
        pytest.fail(
            f"Valid browser event_type {event_type.name} should not raise exceptions"
        )


def test_invalid_event_type_textbook_pdf_zoom_buttons_changed(default_browser_event):
    """Test that a invalid event value does raise a ValidationError
    for browser event type textbook.pdf.zoom.buttons.changed and
    textbook.pdf.page.scrolled
    """
    event = {
        "chapter": f"/asset-v1:{COURSE_ID[10:]}+type@asset+block/test.pdf",
        "page": 1,
    }
    for event_type in [
        EventType.BROWSER_TEXTBOOK_PDF_ZOOM_BUTTONS_CHANGED,
        EventType.BROWSER_TEXTBOOK_PDF_PAGE_SCROLLED,
    ]:
        event["name"] = event_type.name.lower()[8:].replace("_", ".")
        with pytest.raises(ValidationError) as excinfo:
            default_browser_event(event_type, event=json.dumps(event))
        check_error(
            excinfo, "{'direction'} key is required for event", operator.contains
        )

        event["direction"] = "not one of in/out/up/down"
        with pytest.raises(ValidationError) as excinfo:
            default_browser_event(event_type, event=json.dumps(event))
        check_error(excinfo, "direction should be one of", operator.contains)

        event["direction"] = None
        with pytest.raises(ValidationError) as excinfo:
            default_browser_event(event_type, event=json.dumps(event))
        check_error(excinfo, "direction should be one of", operator.contains)
        del event["direction"]


def test_valid_event_type_textbook_pdf_zoom_menu_changed(default_browser_event):
    """Test that a valid event value does not raise a ValidationError
    for browser event type textbook.pdf.zoom.menu.changed
    """
    event = {
        "chapter": f"/asset-v1:{COURSE_ID[10:]}+type@asset+block/test.pdf",
        "page": 1,
        "name": "textbook.pdf.zoom.menu.changed",
        "amount": "1",
    }
    try:
        default_browser_event(
            EventType.BROWSER_TEXTBOOK_PDF_ZOOM_MENU_CHANGED, event=json.dumps(event)
        )
    except ValidationError:
        pytest.fail(
            f"Valid browser event_type textbook.pdf.zoom.menu.changed "
            f"should not raise exceptions"
        )


def test_invalid_event_type_textbook_pdf_zoom_menu_changed(default_browser_event):
    """Test that a invalid event value does raise a ValidationError
    for browser event type textbook.pdf.zoom.menu.changed
    """
    event_type = EventType.BROWSER_TEXTBOOK_PDF_ZOOM_MENU_CHANGED
    event = {
        "chapter": f"/asset-v1:{COURSE_ID[10:]}+type@asset+block/test.pdf",
        "page": 1,
        "name": event_type.name.lower()[8:].replace("_", "."),
    }
    with pytest.raises(ValidationError) as excinfo:
        default_browser_event(event_type, event=json.dumps(event))
    check_error(excinfo, "{'amount'} key is required for event", operator.contains)

    event["amount"] = 1
    with pytest.raises(ValidationError) as excinfo:
        default_browser_event(event_type, event=json.dumps(event))
    check_error(excinfo, "amount should be one of", operator.contains)

    event["amount"] = "1 "
    with pytest.raises(ValidationError) as excinfo:
        default_browser_event(event_type, event=json.dumps(event))
    check_error(excinfo, "amount should be one of", operator.contains)


def test_valid_event_type_textbook_pdf_display_scaled(default_browser_event):
    """Test that a valid event value does not raise a ValidationError
    for browser event type textbook.pdf.display.scaled
    """
    event = {
        "chapter": f"/asset-v1:{COURSE_ID[10:]}+type@asset+block/test.pdf",
        "page": 1,
        "name": "textbook.pdf.display.scaled",
        "amount": 1.1641304347826087,
    }
    try:
        default_browser_event(
            EventType.BROWSER_TEXTBOOK_PDF_DISPLAY_SCALED, event=json.dumps(event)
        )
    except ValidationError:
        pytest.fail(
            "Valid browser event_type textbook.pdf.display.scaled "
            "should not raise exceptions"
        )


def test_invalid_event_type_textbook_pdf_display_scaled(default_browser_event):
    """Test that a invalid event value does raise a ValidationError
    for browser event type textbook.pdf.display.scaled
    """
    event_type = EventType.BROWSER_TEXTBOOK_PDF_DISPLAY_SCALED
    event = {
        "chapter": f"/asset-v1:{COURSE_ID[10:]}+type@asset+block/test.pdf",
        "page": 1,
        "name": event_type.name.lower()[8:].replace("_", "."),
    }
    with pytest.raises(ValidationError) as excinfo:
        default_browser_event(event_type, event=json.dumps(event))
    check_error(excinfo, "{'amount'} key is required for event", operator.contains)

    event["amount"] = "1"
    with pytest.raises(ValidationError) as excinfo:
        default_browser_event(event_type, event=json.dumps(event))
    check_error(excinfo, "amount should be a float integer")
