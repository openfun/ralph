"""
Tests for the Browser event schema
"""
import json
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

from .fixtures.logs import EventType, _event

SCHEMA = BrowserEventSchema()


@pytest.fixture()
def browser_events():
    """Returns a broser event generator that generates size number of events"""
    return lambda size, **kwargs: _event(size, EventType.BROWSER, **kwargs)


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
    with pytest.raises(ValidationError):
        browser_events(1, event_source="not_browser")


def test_valid_session_should_not_raise_exception(browser_events):
    """Test that a valid session does not raise a ValidationError"""
    try:
        browser_events(1, session="")
        browser_events(1, session="The_session_is_32_character_long")
    except ValidationError:
        pytest.fail("Valid browser event session should not raise exceptions")


def test_invalid_session_should_raise_exception(browser_events):
    """Test that a invalid session raise ValidationError"""
    with pytest.raises(ValidationError):
        browser_events(1, session="less_than_32_charactees")
    with pytest.raises(ValidationError):
        browser_events(1, session="The_session_is_more_than_32_character_long")
    with pytest.raises(ValidationError):
        browser_events(1, session=None)


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
    with pytest.raises(ValidationError):
        browser_events(1, page="invalid/url")
    with pytest.raises(ValidationError):
        browser_events(1, page="")
    with pytest.raises(ValidationError):
        browser_events(1, page=None)


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
    with pytest.raises(ValidationError):
        browser_events(1, event_type="not_in_BROWSER_EVENT_TYPE_FIELD")
    with pytest.raises(ValidationError):
        browser_events(1, event_type="page_close", name="not_page_close")
    with pytest.raises(ValidationError):
        browser_events(1, event_type="page_close", name="problem_show")
    with pytest.raises(ValidationError):
        browser_events(1, event_type="book", name="book")


def test_valid_event_with_event_type_page_close(browser_events):
    """Test that a valid event value does not raise a ValidationError"""
    try:
        browser_events(1, event_type="page_close", event="{}")
    except ValidationError:
        pytest.fail("Valid browser event_type `page_close` should not raise exceptions")


def test_invalid_event_type_page_close(browser_events):
    """Test that a invalid event value raise a ValidationError"""
    with pytest.raises(ValidationError):
        browser_events(1, event_type="page_close", event='{"key": "value"}')
    with pytest.raises(ValidationError):
        browser_events(1, event_type="page_close", event="")


def test_valid_event_with_event_type_problem_show(browser_events):
    """Test that a valid event value does not raise a ValidationError"""
    try:
        org_id = "org"
        course_id = "course-v1:org+numeroCours+sessiondCours"
        event = json.dumps(
            {
                "problem": (
                    f"block-v1:{course_id[10:]}+type@problem+block@"
                    "9cc0b13998d74e6ca57b5aa77718b97b"
                )
            }
        )
        browser_events(
            1,
            event_type="problem_show",
            context_args={"org_id": org_id, "course_id": course_id},
            event=event,
        )
    except ValidationError:
        pytest.fail(
            "Valid browser event_type `problem_show` should not raise exceptions"
        )


def test_invalid_event_type_problem_show(browser_events):
    """Test that a invalid event value raise a ValidationError"""
    org_id = "org"
    course_id = "course-v1:org+numeroCours+sessiondCours"
    with pytest.raises(ValidationError):
        event = json.dumps(
            {
                "problem": (
                    f"block-v1:NOTorg+numeroCours+sessiondCours+type@problem+block@"
                    f"9cc0b13998d74e6ca57b5aa77718b97b"
                )
            }
        )
        browser_events(
            1,
            event_type="problem_show",
            context_args={"org_id": org_id, "course_id": course_id},
            event=event,
        )
    with pytest.raises(ValidationError):
        event = json.dumps(
            {
                "NOTproblem": (
                    f"block-v1:{course_id[10:]}+type@problem+block@"
                    "9cc0b13998d74e6ca57b5aa77718b97b"
                )
            }
        )
        browser_events(
            1,
            event_type="problem_show",
            context_args={"org_id": org_id, "course_id": course_id},
            event=event,
        )
    with pytest.raises(ValidationError):
        browser_events(1, event_type="problem_show", event="{}")


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
    with pytest.raises(ValidationError):
        browser_events(1, event_type="problem_check", event="{}")
    with pytest.raises(ValidationError):
        browser_events(
            1, event_type="problem_check", event="invalid URL-encoded string"
        )
    with pytest.raises(ValidationError):
        browser_events(1, event_type="problem_check", event=None)
    with pytest.raises(ValidationError):
        browser_events(1, event_type="problem_check", event=123)


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
    problem_save browser event does raise a ValidationError
    """
    for event_type in ["problem_graded", "problem_reset", "problem_save"]:
        with pytest.raises(ValidationError):
            browser_events(1, event_type=event_type, event=[])
        with pytest.raises(ValidationError):
            browser_events(
                1,
                event_type=event_type,
                event=["input_d9fd0115d0be4fe08281f2eaf361744c_2_1=Spain"],
            )
        with pytest.raises(ValidationError):
            browser_events(
                1,
                event_type=event_type,
                event=[
                    "input_d9fd0115d0be4fe08281f2eaf361744c_2_1=Spain",
                    "foo",
                    "bar",
                ],
            )
        with pytest.raises(ValidationError):
            browser_events(
                1,
                event_type=event_type,
                event=["input_d9fd0115d0be4fe08281f2eaf361744c_2_1", "any_string"],
            )


def test_valid_event_type_seq_goto(browser_events):
    """Test that a valid event value does not raise a ValidationError"""
    try:
        org_id = "org"
        course_id = "course-v1:org+numeroCours+sessiondCours"
        event = json.dumps(
            {
                "new": 1,
                "old": 1,
                "id": (
                    f"block-v1:{course_id[10:]}+type@sequential+block@"
                    "9cc0b13998d74e6ca57b5aa77718b97b"
                ),
            }
        )
        browser_events(
            1,
            event_type="seq_goto",
            context_args={"org_id": org_id, "course_id": course_id},
            event=event,
        )
    except ValidationError:
        pytest.fail("Valid browser event_type `seq_goto` should not raise exceptions")


def test_invalid_event_type_seq_goto(browser_events):
    """Test that a invalid seq_goto browser event does raise a ValidationError"""
    org_id = "org"
    course_id = "course-v1:org+numeroCours+sessiondCours"
    event = {
        "new": 1,
        "old": 1,
        "id": (
            f"block-v1:{course_id[10:]}+type@sequential+block@"
            "9cc0b13998d74e6ca57b5aa77718b97b"
        ),
    }
    with pytest.raises(ValidationError):
        browser_events(1, event_type="seq_goto", event="")
    with pytest.raises(ValidationError):
        # event is not a string
        browser_events(
            1,
            event_type="seq_goto",
            context_args={"org_id": org_id, "course_id": course_id},
            event=event,
        )
    with pytest.raises(ValidationError):
        event["new"] = "not a number"
        browser_events(
            1,
            event_type="seq_goto",
            context_args={"org_id": org_id, "course_id": course_id},
            event=json.dumps(event),
        )
    with pytest.raises(ValidationError):
        event["new"] = 1
        event["id"] = (
            f"block-v1:invalid+course+key+type@sequential+block@"
            "9cc0b13998d74e6ca57b5aa77718b97b"
        )
        browser_events(
            1,
            event_type="seq_goto",
            context_args={"org_id": org_id, "course_id": course_id},
            event=json.dumps(event),
        )
    with pytest.raises(ValidationError):
        event["id"] = f"block-v1:{course_id[10:]}+type@sequential+block@invalid_id"
        browser_events(
            1,
            event_type="seq_goto",
            context_args={"org_id": org_id, "course_id": course_id},
            event=json.dumps(event),
        )
    with pytest.raises(ValidationError):
        event["id"] = (
            f"block-v1:{course_id[10:]}+type@sequential+block@"
            "9cc0b13998d74e6ca57b5aa77718b97b"
        )
        event["invalid_key"] = "invalid_value"
        browser_events(
            1,
            event_type="seq_goto",
            context_args={"org_id": org_id, "course_id": course_id},
            event=json.dumps(event),
        )
    with pytest.raises(ValidationError):
        del event["invalid_key"]
        del event["new"]
        browser_events(
            1,
            event_type="seq_goto",
            context_args={"org_id": org_id, "course_id": course_id},
            event=json.dumps(event),
        )
    with pytest.raises(ValidationError):
        event["new"] = 1
        del event["old"]
        browser_events(
            1,
            event_type="seq_goto",
            context_args={"org_id": org_id, "course_id": course_id},
            event=json.dumps(event),
        )
    with pytest.raises(ValidationError):
        event["old"] = 1
        del event["id"]
        browser_events(
            1,
            event_type="seq_goto",
            context_args={"org_id": org_id, "course_id": course_id},
            event=json.dumps(event),
        )


def test_valid_event_type_seq_next_and_seq_prev(browser_events):
    """Test that a valid event value does not raise a ValidationError"""
    for event_type in ["seq_next", "seq_prev"]:
        try:
            org_id = "org"
            course_id = "course-v1:org+numeroCours+sessiondCours"
            event = json.dumps(
                {
                    "new": 3 if event_type == "seq_next" else 1,
                    "old": 2,
                    "id": (
                        f"block-v1:{course_id[10:]}+type@sequential+block@"
                        "9cc0b13998d74e6ca57b5aa77718b97b"
                    ),
                }
            )
            browser_events(
                1,
                event_type=event_type,
                context_args={"org_id": org_id, "course_id": course_id},
                event=event,
            )
        except ValidationError:
            pytest.fail(
                f"Valid browser event_type `{event_type}`should not raise exceptions"
            )


def test_invalid_event_type_seq_next_and_seq_prev(browser_events):
    """Test that a invalid event value raise a ValidationError"""
    org_id = "org"
    course_id = "course-v1:org+numeroCours+sessiondCours"
    event = {
        "id": (
            f"block-v1:{course_id[10:]}+type@sequential+block@"
            "9cc0b13998d74e6ca57b5aa77718b97b"
        )
    }
    with pytest.raises(ValidationError):
        event["new"] = 1
        event["old"] = 1
        browser_events(
            1,
            event_type="seq_next",
            context_args={"org_id": org_id, "course_id": course_id},
            event=json.dumps(event),
        )
    with pytest.raises(ValidationError):
        browser_events(
            1,
            event_type="seq_prev",
            context_args={"org_id": org_id, "course_id": course_id},
            event=json.dumps(event),
        )
    with pytest.raises(ValidationError):
        event["new"] = 1
        event["old"] = 2
        browser_events(
            1,
            event_type="seq_next",
            context_args={"org_id": org_id, "course_id": course_id},
            event=json.dumps(event),
        )
    with pytest.raises(ValidationError):
        event["new"] = 2
        event["old"] = 1
        browser_events(
            1,
            event_type="seq_prev",
            context_args={"org_id": org_id, "course_id": course_id},
            event=json.dumps(event),
        )
    with pytest.raises(ValidationError):
        event["new"] = 3
        event["old"] = 1
        browser_events(
            1,
            event_type="seq_next",
            context_args={"org_id": org_id, "course_id": course_id},
            event=json.dumps(event),
        )
    with pytest.raises(ValidationError):
        event["new"] = 1
        event["old"] = 3
        browser_events(
            1,
            event_type="seq_prev",
            context_args={"org_id": org_id, "course_id": course_id},
            event=json.dumps(event),
        )


def test_valid_event_type_textbook_pdf_thumbnail_outline_toggled(browser_events):
    """Test that a valid event value does not raise a ValidationError
    for browser events: textbook.pdf.thumbnails.toggled,
    textbook.pdf.outline.toggled and textbook.pdf.page.navigated
    """
    org_id = "org"
    course_id = "course-v1:org+numeroCours+sessiondCours"
    event = {
        "chapter": f"/asset-v1:{course_id[10:]}+type@asset+block/test.pdf",
        "page": 1,
    }
    for event_type in [
        "textbook.pdf.thumbnails.toggled",
        "textbook.pdf.outline.toggled",
        "textbook.pdf.page.navigated",
    ]:
        try:
            event["name"] = event_type
            browser_events(
                1,
                event_type=event_type,
                context_args={"org_id": org_id, "course_id": course_id},
                event=json.dumps(event),
            )
        except ValidationError:
            pytest.fail(
                f"Valid browser event_type `{event_type}`should not raise exceptions"
            )


def test_invalid_event_type_textbook_pdf_thumbnail_outline_toggled(browser_events):
    """Test that a invalid event value does raise a ValidationError"""
    org_id = "org"
    course_id = "course-v1:org+numeroCours+sessiondCours"
    event = {}
    for event_type in [
        "textbook.pdf.thumbnails.toggled",
        "textbook.pdf.outline.toggled",
        "textbook.pdf.page.navigated",
    ]:
        with pytest.raises(ValidationError):
            event["name"] = event_type
            event["page"] = 1
            event["chapter"] = f"/asset-v1:{course_id[10:]}+type@asset+block/test.pdf"
            browser_events(
                1,
                event_type=event_type,
                context_args={"org_id": org_id, "course_id": course_id},
                event=event,
            )
        with pytest.raises(ValidationError):
            del event["page"]
            browser_events(
                1,
                event_type=event_type,
                context_args={"org_id": org_id, "course_id": course_id},
                event=json.dumps(event),
            )
        with pytest.raises(ValidationError):
            event["page"] = "not_integer"
            browser_events(
                1,
                event_type=event_type,
                context_args={"org_id": org_id, "course_id": course_id},
                event=json.dumps(event),
            )
        with pytest.raises(ValidationError):
            event["page"] = "123"
            browser_events(
                1,
                event_type=event_type,
                context_args={"org_id": org_id, "course_id": course_id},
                event=json.dumps(event),
            )
        with pytest.raises(ValidationError):
            event["page"] = -1
            browser_events(
                1,
                event_type=event_type,
                context_args={"org_id": org_id, "course_id": course_id},
                event=json.dumps(event),
            )
        with pytest.raises(ValidationError):
            event["page"] = 132
            del event["name"]
            browser_events(
                1,
                event_type=event_type,
                context_args={"org_id": org_id, "course_id": course_id},
                event=json.dumps(event),
            )
        with pytest.raises(ValidationError):
            event["name"] = "not_event_type"
            browser_events(
                1,
                event_type=event_type,
                context_args={"org_id": org_id, "course_id": course_id},
                event=json.dumps(event),
            )
        with pytest.raises(ValidationError):
            event["name"] = event_type
            del event["chapter"]
            browser_events(
                1,
                event_type=event_type,
                context_args={"org_id": org_id, "course_id": course_id},
                event=json.dumps(event),
            )
        with pytest.raises(ValidationError):
            # chapter does not end with .pdf
            event["chapter"] = f"/asset-v1:{course_id[10:]}+type@asset+block/test.xml"
            browser_events(
                1,
                event_type=event_type,
                context_args={"org_id": org_id, "course_id": course_id},
                event=json.dumps(event),
            )
        with pytest.raises(ValidationError):
            event[
                "chapter"
            ] = f"/asset-v1:{course_id[10:]}+type@not_asset+block/test.pdf"
            browser_events(
                1,
                event_type=event_type,
                context_args={"org_id": org_id, "course_id": course_id},
                event=json.dumps(event),
            )
        with pytest.raises(ValidationError):
            event["chapter"] = f"/asset-v1:invalid+course+key+type@asset+block/test.pdf"
            browser_events(
                1,
                event_type=event_type,
                context_args={"org_id": org_id, "course_id": course_id},
                event=json.dumps(event),
            )
