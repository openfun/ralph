"""
Tests for the Browser event schema
"""
import json
import operator
import urllib.parse

# pylint: disable=redefined-outer-name
import pandas as pd
import pytest
from marshmallow import ValidationError

from ralph.schemas.edx.browser import (
    BROWSER_EVENT_TYPE_FIELD,
    BROWSER_NAME_FIELD,
    BrowserEventSchema,
)

from tests.fixtures.logs import EventType, _event

SCHEMA = BrowserEventSchema()
ORG_ID = "org"
COURSE_ID = "course-v1:org+course+session"
MD5 = "9cc0b13998d74e6ca57b5aa77718b97b"


@pytest.fixture()
def browser_events():
    """Returns a broser event generator that generates size number of events"""
    return lambda size, **kwargs: _event(size, EventType.BROWSER, **kwargs)


@pytest.fixture()
def one_browser_event():
    """Generates one browser event with default org_id and course_id"""

    def _one_browser_event(**kwargs):
        return _event(
            1,
            EventType.BROWSER,
            context_args={"org_id": ORG_ID, "course_id": COURSE_ID},
            **kwargs,
        )

    return _one_browser_event


def check_error(excinfo, message, operator_type=operator.eq):
    """Compare error `excinfo` message with operator_type on `message`"""
    key = next(iter(excinfo.value.messages))
    value = excinfo.value.messages[key][0]
    assert operator_type(value, message)


def test_loading_valid_events_should_not_raise_exceptions():
    """Test that loading valid events does not raise exceptions
    """
    chunks = pd.read_json("tests/data/browser_event.log", lines=True)
    try:
        for _, chunk in chunks.iterrows():
            SCHEMA.load(chunk.to_dict())
    except ValidationError:
        pytest.fail("valid browser events should not raise exceptions")


def test_valid_event_source_should_not_raise_exception(browser_events):
    """Test that a valid event_source not raise a ValidationError"""
    try:
        browser_events(1)
        browser_events(1, event_source="browser")
    except ValidationError:
        pytest.fail("Valid browser event event_source should not raise exceptions")


def test_invalid_event_source_should_raise_exception(browser_events):
    """Test that a invalid event_source raise ValidationError"""
    with pytest.raises(ValidationError) as excinfo:
        browser_events(1, event_source="not_browser")
    check_error(excinfo, "The event event_source field is not `browser`")


def test_valid_session_should_not_raise_exception(browser_events):
    """Test that a valid session does not raise a ValidationError"""
    try:
        browser_events(1, session="")
        browser_events(1, session="The_session_is_32_character_long")
    except ValidationError:
        pytest.fail("Valid browser event session should not raise exceptions")


def test_invalid_session_should_raise_exception(browser_events):
    """Test that a invalid session raise ValidationError"""
    with pytest.raises(ValidationError) as excinfo:
        browser_events(1, session="less_than_32_charactees")
    check_error(excinfo, "Session should be empty or 32 chars long (MD5)")
    with pytest.raises(ValidationError) as excinfo:
        browser_events(1, session="The_session_is_more_than_32_character_long")
    check_error(excinfo, "Session should be empty or 32 chars long (MD5)")
    with pytest.raises(ValidationError) as excinfo:
        browser_events(1, session=None)
    check_error(excinfo, "Field may not be null.")


def test_valid_page_should_not_raise_exception(browser_events):
    """Test that a valid page does not raise a ValidationError"""
    try:
        browser_events(1, page="https://www.fun-mooc.fr/")
        browser_events(1, page="/this/is/a/valid/relative/url")
        browser_events(1, page="/")
    except ValidationError:
        pytest.fail("Valid browser event page should not raise exceptions")


def test_invalid_page_should_raise_exception(browser_events):
    """Test that a invalid page raise ValidationError"""
    with pytest.raises(ValidationError) as excinfo:
        browser_events(1, page="invalid/url")
    check_error(excinfo, "Not a valid URL.")

    with pytest.raises(ValidationError) as excinfo:
        browser_events(1, page="")
    check_error(excinfo, "Not a valid URL.")

    with pytest.raises(ValidationError) as excinfo:
        browser_events(1, page=None)
    check_error(excinfo, "Field may not be null.")


def test_valid_event_type_and_name_should_not_raise_exception(browser_events):
    """Test that a valid event_type does not raise a ValidationError"""
    try:
        for event_type in BROWSER_EVENT_TYPE_FIELD:
            event = browser_events(1, event_type=event_type).iloc[0]
            if event_type != "book":
                assert event["event_type"] == event["name"]
            else:
                assert event["name"] in BROWSER_NAME_FIELD
    except ValidationError:
        pytest.fail("Valid browser event_type should not raise exceptions")


def test_invalid_event_type_and_name_should_raise_exception(browser_events):
    """Test that a invalid event_type_and_name raise ValidationError"""
    with pytest.raises(ValidationError) as excinfo:
        browser_events(1, event_type="not_in_BROWSER_EVENT_TYPE_FIELD")
    check_error(excinfo, "The event name field value is not one of the valid values")

    with pytest.raises(ValidationError) as excinfo:
        browser_events(1, event_type="page_close", name="not_page_close")
    check_error(
        excinfo,
        "The name field should be equal to the event_type when event_type is not `book`",
    )

    with pytest.raises(ValidationError) as excinfo:
        browser_events(1, event_type="page_close", name="problem_show")
    check_error(
        excinfo,
        "The name field should be equal to the event_type when event_type is not `book`",
    )

    with pytest.raises(ValidationError) as excinfo:
        browser_events(1, event_type="book", name="book")
    check_error(excinfo, "The name field is not one of the allowed values")


def test_valid_event_with_event_type_page_close(browser_events):
    """Test that a valid event value does not raise a ValidationError"""
    try:
        browser_events(1, event_type="page_close", event="{}")
    except ValidationError:
        pytest.fail("Valid browser event_type `page_close` should not raise exceptions")


def test_invalid_event_type_page_close(browser_events):
    """Test that a invalid event value raise a ValidationError"""
    with pytest.raises(ValidationError) as excinfo:
        browser_events(1, name="page_close", event='{"key": "value"}')
    check_error(excinfo, "Event should be an empty JSON when name is `page_close`")

    with pytest.raises(ValidationError) as excinfo:
        browser_events(1, name="page_close", event="")
    check_error(excinfo, "Event should be an empty JSON when name is `page_close`")


def test_valid_event_with_event_type_problem_show(one_browser_event):
    """Test that a valid event value does not raise a ValidationError"""
    problem = f"block-v1:{COURSE_ID[10:]}+type@problem+block@{MD5}"
    try:
        event = json.dumps({"problem": problem})
        one_browser_event(event_type="problem_show", event=event)
    except ValidationError:
        pytest.fail(
            "Valid browser event_type `problem_show` should not raise exceptions"
        )


def test_invalid_event_type_problem_show(one_browser_event):
    """Test that a invalid event value raise a ValidationError"""
    problem = f"block-v1:NOTorg+course+session+type@problem+block@{MD5}"
    with pytest.raises(ValidationError) as excinfo:
        event = json.dumps({"problem": problem})
        one_browser_event(event_type="problem_show", event=event)
    check_error(
        excinfo,
        "Event problem should start with `block-v1:org+course+session+type@problem+block@`",
        operator.contains,
    )

    with pytest.raises(ValidationError) as excinfo:
        problem = f"block-v1:{COURSE_ID[10:]}+type@problem+block@{MD5}"
        event = json.dumps({"NOTproblem": problem})
        one_browser_event(event_type="problem_show", event=event)
    check_error(
        excinfo,
        "{'problem'} key is required for event, {'NOTproblem'} key is not valid for event",
    )

    with pytest.raises(ValidationError) as excinfo:
        one_browser_event(event_type="problem_show", event="{}")
    check_error(excinfo, "{'problem'} key is required for event", operator.contains)


def test_valid_event_type_problem_check(browser_events):
    """Test that a valid event value does not raise a ValidationError"""
    event = browser_events(1, event_type="problem_check").iloc[0]["event"]
    assert isinstance(event, str)
    assert len(urllib.parse.parse_qs(event)) >= 1 or event == ""
    try:
        event = ""
        browser_events(1, event_type="problem_check", event=event)
        event = "input_2394233ce59042f6ae67339dd4629fd8_2_1=Spain"
        browser_events(1, event_type="problem_check", event=event)
        event = "input_cc2a00e69f7a4dd8b560f4e48911206f_2_1="
        browser_events(1, event_type="problem_check", event=event)
        event = (
            "input_cc2a00e69f7a4dd8b560f4e48911206f_2_1=&"
            "input_cc2a00e69f7a4dd8b560f4e48911206f_3_1="
        )
        browser_events(1, event_type="problem_check", event=event)
        event = (
            "input_0924f1350d02437da3c4451e1582acd1_2_1%5B%5D=choice_0&"
            "input_0924f1350d02437da3c4451e1582acd1_2_1%5B%5D=choice_1&"
            "input_0924f1350d02437da3c4451e1582acd1_2_1%5B%5D=choice_3&"
            "input_0924f1350d02437da3c4451e1582acd1_3_1%5B%5D=choice_0&"
            "input_0924f1350d02437da3c4451e1582acd1_3_1%5B%5D=choice_1&"
            "input_0924f1350d02437da3c4451e1582acd1_3_1%5B%5D=choice_3"
        )
        browser_events(1, event_type="problem_check", event=event)
    except ValidationError:
        pytest.fail(
            "Valid browser event_type `problem_check` should not raise exceptions"
        )


def test_invalid_event_type_problem_check(browser_events):
    """Test that a invalid problem_check browser event does raise a ValidationError"""
    with pytest.raises(ValidationError) as excinfo:
        browser_events(1, event_type="problem_check", event="{}")
    check_error(excinfo, "Event should be a valid URL-encoded string")
    with pytest.raises(ValidationError) as excinfo:
        browser_events(
            1, event_type="problem_check", event="invalid URL-encoded string"
        )
    check_error(excinfo, "Event should be a valid URL-encoded string")
    with pytest.raises(ValidationError) as excinfo:
        browser_events(1, event_type="problem_check", event=None)
    check_error(excinfo, "Field may not be null.")
    with pytest.raises(ValidationError) as excinfo:
        browser_events(1, event_type="problem_check", event=123)
    check_error(excinfo, "Event should be a valid URL-encoded string")


def test_valid_event_type_problem_graded_or_similar(browser_events):
    """Test that a valid event value does not raise a ValidationError
    for browser events: problem_graded, problem_reset and problem_save
    """
    try:
        for event_type in ["problem_graded", "problem_reset", "problem_save"]:
            event = ["input_d9fd0115d0be4fe08281f2eaf361744c_2_1=Spain", "any string"]
            browser_events(1, event_type=event_type, event=event)
            event = [
                (
                    "input_afa254601f4b48128baf1c3e7054fb59_2_1=1%5E6&"
                    "input_afa254601f4b48128baf1c3e7054fb59_3_1=10"
                ),
                "any string",
            ]
            browser_events(1, event_type=event_type, event=event)
    except ValidationError:
        pytest.fail(
            f"Valid browser event_type `{event_type}` should not raise exceptions"
        )


def test_invalid_event_type_problem_graded_or_similar(browser_events):
    """Test that a invalid problem_graded problem_reset and
    problem_save browser event does raise a ValidationError """
    for event_type in ["problem_graded", "problem_reset", "problem_save"]:
        with pytest.raises(ValidationError) as excinfo:
            browser_events(1, event_type=event_type, event=[])
        check_error(excinfo, "Event should be a two-items list")
        with pytest.raises(ValidationError) as excinfo:
            browser_events(
                1,
                event_type=event_type,
                event=["input_d9fd0115d0be4fe08281f2eaf361744c_2_1=Spain"],
            )
        check_error(excinfo, "Event should be a two-items list")
        with pytest.raises(ValidationError) as excinfo:
            browser_events(
                1,
                event_type=event_type,
                event=[
                    "input_d9fd0115d0be4fe08281f2eaf361744c_2_1=Spain",
                    "foo",
                    "bar",
                ],
            )
        check_error(excinfo, "Event should be a two-items list")
        with pytest.raises(ValidationError) as excinfo:
            browser_events(
                1,
                event_type=event_type,
                event=["input_d9fd0115d0be4fe08281f2eaf361744c_2_1", "any_string"],
            )
        check_error(
            excinfo, "Event list first item should be a valid URL-encoded string"
        )


def test_valid_event_type_seq_goto(one_browser_event):
    """Test that a valid event value does not raise a ValidationError"""
    id_value = f"block-v1:{COURSE_ID[10:]}+type@sequential+block@{MD5}"
    event = json.dumps({"new": 1, "old": 1, "id": id_value})
    try:
        one_browser_event(event_type="seq_goto", event=event)
    except ValidationError:
        pytest.fail("Valid browser event_type `seq_goto` should not raise exceptions")


def test_invalid_event_type_seq_goto_with_unparsable_json(one_browser_event):
    """Test that a invalid seq_goto browser event does raise a ValidationError"""
    with pytest.raises(ValidationError) as excinfo:
        one_browser_event(event_type="seq_goto", event="")
    check_error(excinfo, "Event should contain a parsable JSON string")

    with pytest.raises(ValidationError) as excinfo:
        one_browser_event(event_type="seq_goto", event={"new": 1})
    check_error(excinfo, "Event should contain a parsable JSON string")


def test_invalid_event_type_seq_goto_with_invalid_key_values(one_browser_event):
    """Test that a invalid seq_goto browser event does raise a ValidationError"""
    id_value = f"block-v1:{COURSE_ID[10:]}+type@sequential+block@{MD5}"
    event = {"new": "not a number", "old": 1, "id": id_value}
    with pytest.raises(ValidationError) as excinfo:
        one_browser_event(event_type="seq_goto", event=json.dumps(event))
    check_error(excinfo, "Event new and old fields should be integer")

    event["new"] = 1
    event["id"] = f"block-v1:invalid+course+key+type@sequential+block@{MD5}"
    with pytest.raises(ValidationError) as excinfo:
        one_browser_event(event_type="seq_goto", event=json.dumps(event))
    check_error(excinfo, "The id should start with block-v1:org", operator.contains)

    event["id"] = f"block-v1:{COURSE_ID[10:]}+type@sequential+block@invalid_id"
    with pytest.raises(ValidationError) as excinfo:
        one_browser_event(event_type="seq_goto", event=json.dumps(event))
    check_error(excinfo, "The id should end with a 32 long MD5 hash")


def test_invalid_event_type_seq_goto_with_missing_or_additional_keys(one_browser_event):
    """Test that a invalid seq_goto browser event does raise a ValidationError"""
    id_value = f"block-v1:{COURSE_ID[10:]}+type@sequential+block@{MD5}"
    event = {"old": 1, "id": id_value}
    with pytest.raises(ValidationError) as excinfo:
        one_browser_event(event_type="seq_goto", event=json.dumps(event))
    check_error(excinfo, "{'new'} key is required for event", operator.contains)

    event["new"] = 1
    del event["old"]
    with pytest.raises(ValidationError) as excinfo:
        one_browser_event(event_type="seq_goto", event=json.dumps(event))
    check_error(excinfo, "{'old'} key is required for event", operator.contains)

    event["old"] = 1
    del event["id"]
    with pytest.raises(ValidationError) as excinfo:
        one_browser_event(event_type="seq_goto", event=json.dumps(event))
    check_error(excinfo, "{'id'} key is required for event", operator.contains)
    event["id"] = id_value
    event["invalid_key"] = "invalid_value"
    with pytest.raises(ValidationError) as excinfo:
        one_browser_event(event_type="seq_goto", event=json.dumps(event))
    check_error(excinfo, "{'invalid_key'} key is not valid", operator.contains)


def test_valid_event_type_seq_next_and_seq_prev(one_browser_event):
    """Test that a valid event value does not raise a ValidationError"""
    try:
        for event_type in ["seq_next", "seq_prev"]:
            new = 3 if event_type == "seq_next" else 1
            id_value = f"block-v1:{COURSE_ID[10:]}+type@sequential+block@{MD5}"
            event = json.dumps({"new": new, "old": 2, "id": id_value})
            one_browser_event(event_type=event_type, event=event)
    except ValidationError:
        pytest.fail(
            f"Valid browser event_type `{event_type}`should not raise exceptions"
        )


def test_invalid_event_type_seq_next_and_seq_prev(one_browser_event):
    """Test that a invalid event value raise a ValidationError"""
    event = {"id": (f"block-v1:{COURSE_ID[10:]}+type@sequential+block@{MD5}")}

    with pytest.raises(ValidationError) as excinfo:
        event["new"] = 1
        event["old"] = 1
        one_browser_event(event_type="seq_next", event=json.dumps(event))
    check_error(excinfo, "Event new (1) should be equal to old (1) + diff (1)")

    with pytest.raises(ValidationError) as excinfo:
        one_browser_event(event_type="seq_prev", event=json.dumps(event))
    check_error(excinfo, "Event new (1) should be equal to old (1) + diff (-1)")

    with pytest.raises(ValidationError) as excinfo:
        event["new"] = 1
        event["old"] = 2
        one_browser_event(event_type="seq_next", event=json.dumps(event))
    check_error(excinfo, "Event new (1) should be equal to old (2) + diff (1)")

    with pytest.raises(ValidationError) as excinfo:
        event["new"] = 2
        event["old"] = 1
        one_browser_event(event_type="seq_prev", event=json.dumps(event))
    check_error(excinfo, "Event new (2) should be equal to old (1) + diff (-1)")

    with pytest.raises(ValidationError) as excinfo:
        event["new"] = 3
        event["old"] = 1
        one_browser_event(event_type="seq_prev", event=json.dumps(event))
    check_error(excinfo, "Event new (3) should be equal to old (1) + diff (-1)")

    with pytest.raises(ValidationError) as excinfo:
        event["new"] = 1
        event["old"] = 3
        one_browser_event(event_type="seq_prev", event=json.dumps(event))
    check_error(excinfo, "Event new (1) should be equal to old (3) + diff (-1)")


def test_valid_event_type_textbook_pdf_thumbnail_outline_toggled(one_browser_event):
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
            "textbook.pdf.thumbnails.toggled",
            "textbook.pdf.outline.toggled",
            "textbook.pdf.page.navigated",
        ]:
            event["name"] = event_type
            one_browser_event(event_type=event_type, event=json.dumps(event))
    except ValidationError:
        pytest.fail(
            f"Valid browser event_type `{event_type}`should not raise exceptions"
        )


def test_invalid_event_type_textbook_pdf_thumbnail_outline_toggled(one_browser_event):
    """Test that a invalid event value does raise a ValidationError"""
    event = {}
    for event_type in [
        "textbook.pdf.thumbnails.toggled",
        "textbook.pdf.outline.toggled",
        "textbook.pdf.page.navigated",
    ]:
        with pytest.raises(ValidationError) as excinfo:
            event["name"] = event_type
            event["page"] = 1
            event["chapter"] = f"/asset-v1:{COURSE_ID[10:]}+type@asset+block/test.pdf"
            one_browser_event(event_type=event_type, event=event)
        check_error(excinfo, "Event should contain a parsable JSON string")

        check_invalid_thumbnail_outline_toggled_page(
            one_browser_event, event, event_type
        )
        check_invalid_thumbnail_outline_toggled_name(
            one_browser_event, event, event_type
        )
        check_invalid_thumbnail_outline_toggled_chapter(
            one_browser_event, event, event_type
        )


def check_invalid_thumbnail_outline_toggled_page(one_browser_event, event, event_type):
    """check event page field for textbook.pdf.thumbnails.toggled,
    textbook.pdf.outline.toggled, textbook.pdf.page.navigated """
    with pytest.raises(ValidationError) as excinfo:
        del event["page"]
        one_browser_event(event_type=event_type, event=json.dumps(event))
    check_error(excinfo, "{'page'} key is required for event", operator.contains)

    with pytest.raises(ValidationError) as excinfo:
        event["page"] = "not_integer"
        one_browser_event(event_type=event_type, event=json.dumps(event))
    check_error(excinfo, "Event page should a positive integer")

    with pytest.raises(ValidationError) as excinfo:
        event["page"] = "123"
        one_browser_event(event_type=event_type, event=json.dumps(event))
    check_error(excinfo, "Event page should a positive integer")

    with pytest.raises(ValidationError) as excinfo:
        event["page"] = -1
        one_browser_event(event_type=event_type, event=json.dumps(event))
    check_error(excinfo, "Event page should a positive integer")


def check_invalid_thumbnail_outline_toggled_name(one_browser_event, event, event_type):
    """check event name field for textbook.pdf.thumbnails.toggled,
    textbook.pdf.outline.toggled, textbook.pdf.page.navigated """
    with pytest.raises(ValidationError) as excinfo:
        event["page"] = 132
        del event["name"]
        one_browser_event(event_type=event_type, event=json.dumps(event))
    check_error(excinfo, "{'name'} key is required for event", operator.contains)

    with pytest.raises(ValidationError) as excinfo:
        event["name"] = "not_event_type"
        one_browser_event(event_type=event_type, event=json.dumps(event))
    check_error(excinfo, "Event name should be equal to the browser event name")

    with pytest.raises(ValidationError) as excinfo:
        event["name"] = event_type
        del event["chapter"]
        one_browser_event(event_type=event_type, event=json.dumps(event))
    check_error(excinfo, "{'chapter'} key is required for event", operator.contains)


def check_invalid_thumbnail_outline_toggled_chapter(
    one_browser_event, event, event_type
):
    """check event chapter field for textbook.pdf.thumbnails.toggled,
    textbook.pdf.outline.toggled, textbook.pdf.page.navigated """
    with pytest.raises(ValidationError) as excinfo:
        event["chapter"] = f"/asset-v1:{COURSE_ID[10:]}+type@asset+block/test.xml"
        one_browser_event(event_type=event_type, event=json.dumps(event))
    check_error(excinfo, "Event chapter should end with the .pdf extension")

    with pytest.raises(ValidationError) as excinfo:
        event["chapter"] = f"/asset-v1:{COURSE_ID[10:]}+type@not_asset+block/test.pdf"
        one_browser_event(event_type=event_type, event=json.dumps(event))
    check_error(
        excinfo,
        "Event chapter should begin with /asset-v1:org+course+session+type@asset+block/",
        operator.contains,
    )

    with pytest.raises(ValidationError) as excinfo:
        event["chapter"] = f"/asset-v1:invalid+course+key+type@asset+block/test.pdf"
        one_browser_event(event_type=event_type, event=json.dumps(event))
    check_error(
        excinfo,
        "Event chapter should begin with /asset-v1:org+course+session+type@asset+block/",
        operator.contains,
    )


def test_valid_event_type_textbook_pdf_thumbnail_navigated(one_browser_event):
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
        one_browser_event(event_type=event["name"], event=json.dumps(event))
    except ValidationError:
        pytest.fail(
            f"Valid browser event_type textbook.pdf.thumbnail.navigated"
            f"should not raise exceptions"
        )


def test_invalid_event_type_textbook_pdf_thumbnail_navigated(one_browser_event):
    """Test that a invalid event value does raise a ValidationError
    for browser events: textbook.pdf.thumbnail.navigated
    """
    event = {
        "chapter": f"/asset-v1:{COURSE_ID[10:]}+type@asset+block/test.pdf",
        "page": 1,
        "name": "textbook.pdf.thumbnail.navigated",
    }
    with pytest.raises(ValidationError) as excinfo:
        one_browser_event(
            event_type="textbook.pdf.thumbnail.navigated", event=json.dumps(event)
        )
    check_error(
        excinfo, "{'thumbnail_title'} key is required for event", operator.contains
    )
    with pytest.raises(ValidationError) as excinfo:
        event["thumbnail_title"] = 123
        one_browser_event(
            event_type="textbook.pdf.thumbnail.navigated", event=json.dumps(event)
        )
    check_error(excinfo, "thumbnail_title should be a string")


def test_valid_event_type_textbook_pdf_zoom_buttons_changed(one_browser_event):
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
            "textbook.pdf.zoom.buttons.changed",
            "textbook.pdf.page.scrolled",
        ]:
            event["name"] = event_type
            event["direction"] = "in" if event_type[-7:] == "changed" else "up"
            one_browser_event(event_type=event_type, event=json.dumps(event))

            event["direction"] = "out" if event_type[-7:] == "changed" else "down"
            one_browser_event(event_type=event_type, event=json.dumps(event))
    except ValidationError:
        pytest.fail(
            f"Valid browser event_type {event_type} should not raise exceptions"
        )


def test_invalid_event_type_textbook_pdf_zoom_buttons_changed(one_browser_event):
    """Test that a invalid event value does raise a ValidationError
    for browser event type textbook.pdf.zoom.buttons.changed and
    textbook.pdf.page.scrolled
    """
    event = {
        "chapter": f"/asset-v1:{COURSE_ID[10:]}+type@asset+block/test.pdf",
        "page": 1,
    }
    for event_type in [
        "textbook.pdf.zoom.buttons.changed",
        "textbook.pdf.page.scrolled",
    ]:
        event["name"] = event_type
        with pytest.raises(ValidationError) as excinfo:
            one_browser_event(event_type=event_type, event=json.dumps(event))
        check_error(
            excinfo, "{'direction'} key is required for event", operator.contains
        )

        event["direction"] = "not one of in/out/up/down"
        with pytest.raises(ValidationError) as excinfo:
            one_browser_event(event_type=event_type, event=json.dumps(event))
        check_error(excinfo, "direction should be one of", operator.contains)

        event["direction"] = None
        with pytest.raises(ValidationError) as excinfo:
            one_browser_event(event_type=event_type, event=json.dumps(event))
        check_error(excinfo, "direction should be one of", operator.contains)
        del event["direction"]


def test_valid_event_type_textbook_pdf_zoom_menu_changed(one_browser_event):
    """Test that a valid event value does not raise a ValidationError
    for browser event type textbook.pdf.zoom.menu.changed
    """
    event = {
        "chapter": f"/asset-v1:{COURSE_ID[10:]}+type@asset+block/test.pdf",
        "page": 1,
        "name": "textbook.pdf.zoom.menu.changed",
        "amaunt": "1",
    }
    try:
        one_browser_event(event_type=event["name"], event=json.dumps(event))
    except ValidationError:
        pytest.fail(
            f"Valid browser event_type textbook.pdf.zoom.menu.changed "
            f"should not raise exceptions"
        )


def test_invalid_event_type_textbook_pdf_zoom_menu_changed(one_browser_event):
    """Test that a invalid event value does raise a ValidationError
    for browser event type textbook.pdf.zoom.menu.changed
    """
    event_type = "textbook.pdf.zoom.menu.changed"
    event = {
        "chapter": f"/asset-v1:{COURSE_ID[10:]}+type@asset+block/test.pdf",
        "page": 1,
        "name": event_type,
    }
    with pytest.raises(ValidationError) as excinfo:
        one_browser_event(event_type=event_type, event=json.dumps(event))
    check_error(excinfo, "{'amaunt'} key is required for event", operator.contains)

    event["amaunt"] = 1
    with pytest.raises(ValidationError) as excinfo:
        one_browser_event(event_type=event_type, event=json.dumps(event))
    check_error(excinfo, "amaunt should be one of", operator.contains)

    event["amaunt"] = "1 "
    with pytest.raises(ValidationError) as excinfo:
        one_browser_event(event_type=event_type, event=json.dumps(event))
    check_error(excinfo, "amaunt should be one of", operator.contains)
