"""
Tests for the event fixture
"""
import json
import random
import urllib.parse

import pandas as pd

from .fixtures.event.base import TiedEventField
from .fixtures.logs import EVENT_TYPES, EventType


def test_event_should_return_a_data_frame(event):
    """check that the fixture returns a DataFrame of needed length"""
    for event_type in EVENT_TYPES:
        events = event(10, event_type)
        assert isinstance(events, pd.DataFrame)
        assert isinstance(events.iloc[0], pd.Series)
        assert isinstance(events.iloc[0]["context"], dict)
        assert len(events) == 10


def test_event_should_update_values_for_each_line(event):
    """check that the fixture dont have much identical fields"""
    for event_type in EVENT_TYPES:
        events = event(30, event_type)
        usernames = events["username"].unique()
        org_ids = events["context"].apply(lambda x: x["org_id"]).unique()
        user_ids = events["context"].apply(lambda x: x["user_id"]).unique()
        assert len(usernames) > 3
        assert len(org_ids) > 3
        assert len(user_ids) > 3
        if event_type in ["server", "browser"]:
            assert sum(usernames == "") > 0
            assert sum(org_ids == "") > 0
            assert sum(user_ids == "") > 0
            assert pd.isnull(user_ids).any()
        else:
            # usernames and org_ids are not emptiable
            # for triggered events
            assert sum(usernames == "") == 0
            assert sum(org_ids == "") == 0


def test_event_should_not_contain_excluded_fields(event):
    """check that the fixture do not contain any excluded parameters"""
    for event_type in EVENT_TYPES:
        events = event(1, event_type)
        exluded = [
            "sub_type",
            "args",
            "kwargs",
            "optional",
            "nullable",
            "emptiable_str",
            "emptiable_dict",
            "is_anonymous",
            "set_all_null",
            "set_all_filled",
            "remove_optional",
            "keep_optional",
            "book_event_type",
            "set_randomization_seed",
            "set_student_answers",
        ]
        assert not any(field in events.columns for field in exluded)


def test_server_event_event_type_field_should_be_equal_to_context_path_field(event):
    """check that the server event "event_type" is equal to
    context[path]
    """
    events = event(1, EventType.SERVER)
    assert events.iloc[0]["event_type"] == events.iloc[0]["context"]["path"]


def test_server_event_context_field_course_user_tags_is_optional(event):
    """check that the server event has the optional context
    course_user_tags field, which might be missing sometimes
    """
    events = event(10, EventType.SERVER)
    course_user_tags = events["context"].apply(lambda x: "course_user_tags" in x)
    assert sum(course_user_tags) > 0
    assert sum(course_user_tags) < 10


def test_browser_event_should_not_contain_context_course_user_tags(event):
    """check that the browser event context do not contain the
    course_user_tags field
    """
    events = event(10, "browser")
    course_user_tags = events["context"].apply(lambda x: "course_user_tags" in x)
    assert sum(course_user_tags) == 0


def test_server_event_should_contain_empty_fields_for_anonymous_user(event):
    """check that the server event returns empty fields when called
    with is_anonymous=True option:
    empty username / ip / agent / referer / accept_language
    empty context[course_id / org_id]
    abcent context[course_user_tags]
    null context[user_id]
    """
    events = event(20, EventType.SERVER, is_anonymous=True)
    is_field_empty = events == ""
    is_field_empty = is_field_empty.any()
    user_ids = events["context"].apply(lambda x: x["user_id"]).unique()
    course_user_tags = (
        events["context"].apply(lambda x: "course_user_tags" in x).unique()
    )
    assert (events == "").all()["username"]
    assert is_field_empty["ip"]
    assert is_field_empty["agent"]
    assert is_field_empty["referer"]
    assert is_field_empty["accept_language"]
    assert is_field_empty["referer"]
    assert len(user_ids) == 1
    assert user_ids[0] is None
    assert len(course_user_tags) == 1
    assert not course_user_tags[0]


def test_event_fields_should_be_overridable(event):
    """check that the events can be altered manualy"""
    # Setting custom values for first level fields
    for event_type in EVENT_TYPES:
        events = event(10, event_type, ip="0.0.0.0.0", username="toto")
        assert sum(events["ip"] == "0.0.0.0.0") == 10
        assert sum(events["username"] == "toto") == 10


def test_event_nested_fields_should_be_overridable(event):
    """check that the event nested fields can be altered manualy"""
    for event_type in EVENT_TYPES:
        events = event(
            10,
            event_type,
            context={"course_id": "course-v1:CourseOrg+Coursnumber+CoursSession"},
        )
        course_ids = events["context"].apply(lambda x: x["course_id"])
        assert sum(course_ids == "course-v1:CourseOrg+Coursnumber+CoursSession") == 10


def test_browser_context_path_should_be_overridable(event):
    """Although we define explicitly the path as '/event' in the
    BrowserEvent class, we should be able to override it.
    """
    events = event(1, EventType.BROWSER, context={"path": "/not_event"})["context"]
    assert events.iloc[0]["path"] == "/not_event"


def test_event_fields_should_be_dynamically_overridable(event):
    """check that event fields can be overriden dynamicaly using a
    value generating function
    """

    def value_generator():
        return random.randint(30000, 30005)

    for event_type in EVENT_TYPES:
        random.seed(1)
        events = event(
            10, event_type, context={"user_id": TiedEventField(value_generator)}
        )
        values = pd.Series(
            [30001, 30004, 30000, 30002, 30000, 30003, 30003, 30003, 30005, 30003]
        )
        assert (events["context"].apply(lambda x: x["user_id"]) == values).all()


def test_event_fields_should_be_removable(event):
    """check that event fields can be removed on demand"""
    for event_type in EVENT_TYPES:
        events = event(
            10, event_type, username=TiedEventField(lambda: "", removed=True)
        )
        assert "username" not in events.columns


def test_event_fields_should_be_null_or_empty_when_set_all_null_is_used(event):
    """check that when the option set_all_null is present - all fields
    that are allowed to be set null/empty are set to null/empty
    """
    for event_type in EVENT_TYPES:
        events = event(10, event_type, "set_all_null")
        assert (events["ip"] == "").all()
        assert (events["agent"] == "").all()
        assert (events["referer"] == "").all()
        assert (events["accept_language"] == "").all()
        if event_type in ["server", "browser"]:
            assert events["context"].apply(lambda x: x["user_id"] is None).all()
        course_user_tags = events["context"].apply(
            lambda x: x.get("course_user_tags", {})
        )
        assert (course_user_tags == {}).all()
        assert not (events["time"] == "").any()
        if event_type in ["server", "browser"]:
            assert (events["username"] == "").all()
            if event_type == "browser":
                assert (events["session"] == "").all()
        else:
            # username is not emptiable for triggered events
            assert not (events["username"] == "").any()
            # but context[module[display_name]] is emptiable
            assert (
                events["context"]
                .apply(lambda x: x["module"]["display_name"] == "")
                .all()
            )


def test_event_fields_should_be_not_null_or_empty_when_set_all_filled_is_used(event):
    """check that when the option set_all_filled is present - all fields
    that are allowed to be not null/empty are filled
    """
    for event_type in EVENT_TYPES:
        events = event(10, event_type, "set_all_filled")
        assert not (events["username"] == "").any()
        assert not (events["ip"] == "").any()
        assert not (events["agent"] == "").any()
        assert not (events["referer"] == "").any()
        assert not (events["accept_language"] == "").any()
        user_ids = events["context"].apply(lambda x: x["user_id"])
        assert not pd.isnull(user_ids).any()
        course_user_tags = events["context"].apply(
            lambda x: x.get("course_user_tags", None)
        )
        assert not (course_user_tags == {}).any()
        assert not events["context"].apply(lambda x: x["user_id"] is None).any()
        if event_type == "server":
            # despite the set_all_filled option the page field for
            # server events should be keept null
            assert pd.isnull(events["page"]).all()
        elif event_type == "browser":
            assert not (events["session"] == "").any()
        else:
            assert (
                not events["context"]
                .apply(lambda x: x["module"]["display_name"] == "")
                .any()
            )


def test_event_optional_fields_should_be_removed_when_remove_optional_is_used(event):
    """check that when the option remove_optional is present - all
    optional fields are removed
    """
    for event_type in EVENT_TYPES:
        if event_type == "browser":
            continue
        events = event(10, event_type, "remove_optional")
        course_user_tags = events["context"].apply(lambda x: "course_user_tags" in x)
        assert sum(course_user_tags) == 0


def test_event_optional_fields_should_be_keept_when_keep_optional_is_used(event):
    """check that when the option keep_optional is present - all
    optional fields are keept
    """
    for event_type in EVENT_TYPES:
        if event_type == "browser":
            continue
        events = event(10, event_type, "keep_optional")
        course_user_tags = events["context"].apply(lambda x: "course_user_tags" in x)
        assert sum(course_user_tags) == 10


def test_browser_event_path_and_name_field(event):
    """check that the event path field is "/event" and the name field
    is equal to the event_type field
    """
    events = event(1, EventType.BROWSER)
    assert events.iloc[0]["context"]["path"] == "/event"
    assert events.iloc[0]["name"] == events.iloc[0]["event_type"]


def test_browser_event_of_sub_type_problem_show(event):
    """check the problem_show browser event"""
    events = event(1, EventType.BROWSER, sub_type="problem_show")
    assert isinstance(events.iloc[0]["event"], str)
    parsed_json = json.loads(events.iloc[0]["event"])
    assert "problem" in parsed_json
    assert "@problem+block@" in parsed_json["problem"]


def test_browser_event_of_sub_type_problem_check(event):
    """"check the problem_check browser event"""
    events = event(1, EventType.BROWSER, sub_type="problem_check")
    assert isinstance(events.iloc[0]["event"], str)
    assert len(urllib.parse.parse_qs(events.iloc[0]["event"])) >= 1 or (
        events.iloc[0]["event"] == ""
    )


def test_browser_event_of_sub_type_problem_graded_or_similar(event):
    """"check the problem_graded browser event and stucturwise similar
    browser events problem_reset and problem_save
    """
    for sub_type in ["problem_graded", "problem_reset", "problem_save"]:
        events = event(1, EventType.BROWSER, sub_type=sub_type)
        assert isinstance(events.iloc[0]["event"], list)
        assert len(events.iloc[0]["event"]) == 2
        assert len(urllib.parse.parse_qs(events.iloc[0]["event"][0])) >= 1 or (
            events.iloc[0]["event"][0] == ""
        )


def test_browser_event_of_sub_type_seq_goto(event):
    """check the seq_goto browser event"""
    events = event(1, EventType.BROWSER, sub_type="seq_goto")
    assert isinstance(events.iloc[0]["event"], str)
    parsed_json = json.loads(events.iloc[0]["event"])
    assert "new" in parsed_json
    assert "old" in parsed_json
    assert "id" in parsed_json
    assert "@sequential+block@" in parsed_json["id"]


def test_browser_event_of_sub_type_seq_next_and_seq_prev(event):
    """check the seq_next browser event"""
    for sub_type in ["seq_next", "seq_prev"]:
        events = event(1, EventType.BROWSER, sub_type=sub_type)
        assert isinstance(events.iloc[0]["event"], str)
        parsed_json = json.loads(events.iloc[0]["event"])
        value = 1 if sub_type == "seq_next" else -1
        assert parsed_json["new"] == parsed_json["old"] + value


def check_textbook_pdf_name_and_chapter(events, fields, sub_type):
    """helper function for textbook_pdf* related test"""
    assert isinstance(events.iloc[0]["event"], str)
    parsed_json = json.loads(events.iloc[0]["event"])
    assert len(parsed_json) == len(fields)
    for field in fields:
        assert field in parsed_json
    assert "/asset-v1:" in parsed_json["chapter"]
    assert "+type@asset+block/" in parsed_json["chapter"]
    assert parsed_json["chapter"][-4:] == ".pdf"
    assert parsed_json["name"] == sub_type


def test_browser_event_of_sub_type_textbook_pdf_thumbnail_outline_toggled(event):
    """check the textbook.pdf.thumbnails.toggled,
    textbook.pdf.outline.toggled and textbook.pdf.page.navigated
    browser event
    """
    for sub_type in [
        "textbook.pdf.thumbnails.toggled",
        "textbook.pdf.outline.toggled",
        "textbook.pdf.page.navigated",
    ]:
        events = event(1, EventType.BROWSER, sub_type=sub_type)
        fields = ["name", "page", "chapter"]
        check_textbook_pdf_name_and_chapter(events, fields, sub_type)


def test_browser_event_of_sub_type_textbook_pdf_thumbnail_navigated(event):
    """check the textbook.pdf.thumbnail.navigated browser event"""
    sub_type = "textbook.pdf.thumbnail.navigated"
    events = event(1, EventType.BROWSER, sub_type=sub_type)
    fields = ["name", "page", "chapter", "thumbnail_title"]
    check_textbook_pdf_name_and_chapter(events, fields, sub_type)


def test_browser_event_of_sub_type_textbook_pdf_zoom_buttons_changed(event):
    """check the textbook.pdf.zoom.buttons.changed browser event
    and the textbook.pdf.page.scrolled browser event
    """
    for sub_type in ["textbook.pdf.zoom.buttons.changed", "textbook.pdf.page.scrolled"]:
        events = event(15, "browser", sub_type=sub_type)
        fields = ["name", "page", "chapter", "direction"]
        check_textbook_pdf_name_and_chapter(events, fields, sub_type)
        direction = events["event"].apply(lambda x: json.loads(x)["direction"])
        if sub_type == "textbook.pdf.zoom.buttons.changed":
            direction_out = direction == "out"
            direction_in = direction == "in"
        else:
            direction_out = direction == "up"
            direction_in = direction == "down"
        assert sum(direction_in) > 0
        assert sum(direction_out) > 0
        assert sum(direction_in) + sum(direction_out) == len(direction)


def test_browser_event_of_sub_type_textbook_pdf_zoom_menu_changed(event):
    """check the textbook.pdf.zoom.menu.changed browser event"""
    sub_type = "textbook.pdf.zoom.menu.changed"
    events = event(10, "browser", sub_type=sub_type)
    fields = ["name", "page", "chapter", "amaunt"]
    check_textbook_pdf_name_and_chapter(events, fields, sub_type)
    direction = events["event"].apply(lambda x: json.loads(x)["amaunt"])
    permitted_values = [
        "0.5",
        "0.75",
        "1",
        "1.25",
        "1.5",
        "2",
        "3",
        "4",
        "page-actual",
        "auto",
        "page-width",
        "page-fit",
    ]
    direction.apply(lambda x: x in permitted_values)
    assert direction.all()


def test_browser_event_of_sub_type_textbook_pdf_display_scaled(event):
    """check the textbook.pdf.display.scaled browser event"""
    sub_type = "textbook.pdf.display.scaled"
    events = event(10, "browser", sub_type=sub_type)
    fields = ["name", "page", "chapter", "amaunt"]
    check_textbook_pdf_name_and_chapter(events, fields, sub_type)


def test_browser_event_of_sub_type_book_with_textbook_pdf_page_loaded(event):
    """check the book browser event with and without
    book_event_type textbook.pdf.page.loaded"""
    sub_type = "book"
    event_without_book_event_type = event(1, EventType.BROWSER, sub_type=sub_type)
    event_with_book_event_type = event(
        1,
        EventType.BROWSER,
        sub_type=sub_type,
        book_event_type="textbook.pdf.page.loaded",
    )
    fields = ["name", "chapter", "type", "old", "new"]
    for events in [event_without_book_event_type, event_with_book_event_type]:
        check_textbook_pdf_name_and_chapter(events, fields, "textbook.pdf.page.loaded")
        assert json.loads(events.iloc[0]["event"])["type"] == "gotopage"


def test_browser_event_of_sub_type_book_with_textbook_pdf_page_navigatednext(event):
    """check the book browser event with book_event_type
    textbook.pdf.page.navigatednext"""
    sub_type = "book"
    events = event(
        10,
        EventType.BROWSER,
        sub_type=sub_type,
        book_event_type="textbook.pdf.page.navigatednext",
    )
    fields = ["name", "chapter", "type", "new"]
    check_textbook_pdf_name_and_chapter(
        events, fields, "textbook.pdf.page.navigatednext"
    )
    _type = events["event"].apply(
        lambda x: json.loads(x)["type"] in ["prevpage", "nextpage"]
    )
    assert _type.all()


def test_browser_event_of_sub_type_book_with_textbook_pdf_search(event):
    """check the book browser event with book_event_types:
    textbook.pdf.search.executed,
    textbook.pdf.search.highlight.toggled,
    textbook.pdf.search.navigatednext and
    textbook.pdf.searchcasesensitivity.toggled
    """
    sub_type = "book"
    for book_event_type in [
        "textbook.pdf.search.executed",
        "textbook.pdf.search.highlight.toggled",
        "textbook.pdf.search.navigatednext",
        "textbook.pdf.searchcasesensitivity.toggled",
    ]:
        events = event(
            10, EventType.BROWSER, sub_type=sub_type, book_event_type=book_event_type,
        )
        fields = [
            "name",
            "chapter",
            "caseSensitive",
            "highlightAll",
            "page",
            "query",
            "status",
        ]
        boolean_fields = ["caseSensitive", "highlightAll"]
        if book_event_type == "textbook.pdf.search.navigatednext":
            fields.append("findprevious")
            boolean_fields.append("findprevious")

        check_textbook_pdf_name_and_chapter(events, fields, book_event_type)
        for boolean_field in boolean_fields:
            field = events["event"].apply(
                lambda x, b=boolean_field: json.loads(x)[b] in [True, False]
            )
            assert field.all()
        for emptiable_field in ["status", "query"]:
            field = events["event"].apply(
                lambda x, e=emptiable_field: json.loads(x)[e] == ""
            )
            assert 0 < sum(field) < 10


def test_triggered_event_context_module_should_be_present(event):
    """check that context module is present in triggered events"""
    triggered_events = ["demandhint_displayed", "problem_check"]
    for event_name in triggered_events:
        events = event(20, event_name)
        module = events["context"].apply(lambda x: x["module"])
        assert len(module) == 20
        assert module.apply(lambda x: "display_name" in x and "usage_key" in x).all()
        empty_display_count = sum(module.apply(lambda x: x["display_name"] == ""))
        assert 0 < empty_display_count < 20


def test_event_edx_problem_hint_demandhint_displayed(event):
    """check the edx.problem.hint.demandhint_displayed
    triggered event
    """
    events = event(1, EventType.DEMANDHINT_DISPLAYED).iloc[0]["event"]
    fields = ["hint_index", "module_id", "hint_text", "hint_len"]
    for field in fields:
        assert field in events
    assert len(events) == len(fields)
    events = event(10, EventType.DEMANDHINT_DISPLAYED)["event"]
    assert events.apply(lambda x: x["hint_len"] - x["hint_index"] >= 0).all()


def test_event_edx_problem_hint_demandhint_displayed_should_be_overridable(event):
    """check that we can override a part of the `event` field of the
    edx.problem.hint.demandhint_displayed triggered event
    """
    events = event(1, EventType.DEMANDHINT_DISPLAYED, event={"hint_index": 1000}).iloc[
        0
    ]["event"]
    fields = ["hint_index", "module_id", "hint_text", "hint_len"]
    for field in fields:
        assert field in events
    assert len(events) == len(fields)
    assert events["hint_index"] == 1000


def test_event_problem_check_correct_map(event):
    """checks the validity of the correct_map field
    of a problem_check event
    """
    events = event(10, EventType.PROBLEM_CHECK)
    correct_map_fields = [
        "correctness",
        "npoints",
        "msg",
        "hint",
        "hintmode",
        "queuestate",
        "answervariable",
    ]
    for events_event in events["event"]:
        assert len(events_event["correct_map"]) > 0
        for field in correct_map_fields:
            assert field in correct_map_fields
            for correct_map_key in events_event["correct_map"]:
                value = events_event["correct_map"][correct_map_key]
                assert value["correctness"] in [
                    "correct",
                    "incorrect",
                    "partially-correct",
                ]
                assert value["npoints"] is None or isinstance(value["npoints"], int)
                assert isinstance(value["msg"], str)
                assert isinstance(value["hint"], str)
                assert value["hintmode"] in [None, "on_request", "always"]
                assert (
                    value["queuestate"] is None
                    or "key" in value["queuestate"]
                    and ("time" in value["queuestate"])
                )


def test_event_problem_check_correct_map_should_be_overridable(event):
    """check that we can override the event `correct_map` entierly
    by specifying it as a kwargs parameter
    """
    events = event(10, EventType.PROBLEM_CHECK, event={"correct_map": {"key": "value"}})
    assert events.iloc[0]["event"]["correct_map"] == {"key": "value"}


def test_event_problem_check_with_set_nb_of_questions_option(event):
    """check that we can specify the number of needed questions for the
    problem_check event"""
    events = event(10, EventType.PROBLEM_CHECK, event={"set_nb_of_questions": 2})
    assert events["event"].apply(lambda x: len(x["correct_map"]) == 2).all()


def test_problem_check_problem_id_field(event):
    """check that the problem_id field is equal to the
    context module usage_key field
    """
    events = event(1, EventType.PROBLEM_CHECK).iloc[0]
    assert events["context"]["module"]["usage_key"] == events["event"]["problem_id"]


def test_problem_check_set_nb_of_answers_option(event):
    """check that we can set the number of answers for the
    problem_check event
    """
    events = event(10, EventType.PROBLEM_CHECK, event={"set_nb_of_answers": 0})
    assert events["event"].apply(lambda x: x["answers"] == {}).all()


def test_problem_check_set_answer_types_options(event):
    """check that we can alter the answers with the
    set_answer_types options
    """
    events = event(10, EventType.PROBLEM_CHECK, event={"set_answer_types": "EMPTY"})
    for events_event in events["event"]:
        for key in events_event["answers"]:
            assert events_event["answers"][key] == ""

    events = event(
        10, EventType.PROBLEM_CHECK, event={"set_answer_types": "MULTIPLE_CHOICE"}
    )
    events.append(event(10, "problem_check", event={"set_answer_types": "DROP_DOWN"}))
    for events_event in events["event"]:
        for key in events_event["answers"]:
            assert events_event["answers"][key] != ""
            assert isinstance(events_event["answers"][key], str)

    events = event(
        10, EventType.PROBLEM_CHECK, event={"set_answer_types": "CHECKBOXES"}
    )
    for events_event in events["event"]:
        for key in events_event["answers"]:
            assert isinstance(events_event["answers"][key], list)

    events = event(
        10, EventType.PROBLEM_CHECK, event={"set_answer_types": "NUMERICAL_INPUT"}
    )
    for events_event in events["event"]:
        for key in events_event["answers"]:
            try:
                int(events_event["answers"][key])
            except ValueError:
                assert False

    events = event(10, EventType.PROBLEM_CHECK, event={"set_answer_types": lambda: 123})
    for events_event in events["event"]:
        for key in events_event["answers"]:
            assert events_event["answers"][key] == 123


def test_problem_check_event_should_have_empty_state_when_attempts_is_one(event):
    """check that on the first attempt the state contains empty values"""
    events = event(10, EventType.PROBLEM_CHECK, event={"attempts": 1})
    states = events["event"].apply(lambda x: x["state"])
    assert states.apply(lambda x: x["student_answers"] == {}).all()
    assert states.apply(lambda x: x["correct_map"] == {}).all()
    assert states.apply(lambda x: x["done"] is None).all()


def test_event_problem_check_seed_field(event):
    """check that the problem_check event seed field is present and
    in the correct value range
    """
    events = event(10, EventType.PROBLEM_CHECK)
    seed = events["event"].apply(lambda x: x["state"]["seed"])
    assert len(seed) == 10
    assert not pd.isnull(seed).any()
    assert (seed >= 0).all()
    assert (seed < 1000).all()


def test_event_problem_check_seed_field_with_set_randomization_seed_option(event):
    """check the problem_check event seed field value when the
    set_randomization_seed option is set
    """
    events = event(
        10, EventType.PROBLEM_CHECK, event={"set_randomization_seed": "NEVER"}
    )
    seed = events["event"].apply(lambda x: x["state"]["seed"])
    assert (seed == 1).all()
    events = event(
        10, EventType.PROBLEM_CHECK, event={"set_randomization_seed": "PER_STUDENT"}
    )
    seed = events["event"].apply(lambda x: x["state"]["seed"])
    assert (seed < 20).all()
    assert (seed >= 0).all()
    events = event(
        10, EventType.PROBLEM_CHECK, event={"set_randomization_seed": "OTHER"}
    )
    seed = events["event"].apply(lambda x: x["state"]["seed"])
    assert (seed < 1000).all()
    assert (seed >= 0).all()


def test_event_problem_check_student_answers_field(event):
    """check that the problem_check student answers field is
    present and in the correct value range
    """
    events = event(20, EventType.PROBLEM_CHECK)
    student_answers = events["event"].apply(lambda x: x["state"]["student_answers"])
    assert (student_answers == {}).any()
    assert student_answers.apply(
        lambda x: False if x == {} else isinstance(list(x)[0], str)
    ).any()


def test_event_problem_check_with_set_nb_of_answers_option(event):
    """check that we can control the number of answers with the
    set_nb_of_answers option
    """
    events = event(
        10,
        EventType.PROBLEM_CHECK,
        event={"set_nb_of_answers": 1, "set_nb_of_questions": 1},
    )
    student_answers = events["event"].apply(lambda x: x["answers"])
    assert student_answers.apply(lambda x: len(x) == 1).all()


def test_event_feedback_displayed_correctness_field_should_alter_hint_label(event):
    """check that when correctness is True the hint_label is `Correct`
    for the edx.problem.hint.feedback_displayed event
    """
    events = event(5, EventType.FEEDBACK_DISPLAYED)
    for events_event in events["event"]:
        if events_event["correctness"]:
            assert events_event["hint_label"] == "Correct"
        else:
            assert events_event["hint_label"] != "Correct"
    events = event(5, EventType.FEEDBACK_DISPLAYED, event={"correctness": True})
    assert events["event"].apply(lambda x: x["hint_label"] == "Correct").all()


def test_event_feedback_displayed_problem_part_id_field_should_contain_the_module_id(
    event,
):
    """check that the problem_part_id contains the module_id
    for the edx.problem.hint.feedback_displayed event
    """
    events = event(1, EventType.FEEDBACK_DISPLAYED).iloc[0]["event"]
    assert events["problem_part_id"][:32] == events["module_id"][-32:]


def test_event_feedback_displayed_should_be_altered_when_question_type_is_set(event):
    """check the outcome of the edx.problem.hint.feedback_displayed event
    for each of the possible question_type settings
    """
    single_hint_responses = [
        "optionresponse",
        "multiplechoiceresponse",
        "numericalresponse",
        "stringresponse",
    ]
    for question_type in single_hint_responses:
        events = event(
            5, EventType.FEEDBACK_DISPLAYED, event={"question_type": question_type}
        )["event"]
        assert events.apply(lambda x, q=question_type: x["question_type"] == q).all()
        assert events.apply(
            lambda x: len(x["hints"]) == 1 and isinstance(x["hints"][0]["text"], str)
        ).all()

    events = event(
        5,
        EventType.FEEDBACK_DISPLAYED,
        event={"question_type": "choiceresponse", "trigger_type": "single"},
    )["event"]

    assert events.apply(lambda x: x["trigger_type"] == "single").all()
    assert events.apply(
        lambda x: len(x["hints"]) > 1 and "trigger" in x["hints"][0]
    ).any()

    events = event(
        5,
        EventType.FEEDBACK_DISPLAYED,
        event={"question_type": "choiceresponse", "trigger_type": "compound"},
    )["event"]
    assert events.apply(lambda x: x["trigger_type"] == "compound").all()
    for events_event in events:
        assert len(events_event["hints"]) == 1
        assert len(events_event["hints"][0]["trigger"]) == len(
            events_event["student_answer"]
        )


def test_event_feedback_displayed_student_answer_field_might_be_an_empty_array(event):
    """check that sometimes the student_answer field is an empty array for the
    edx.problem.hint.feedback_displayed event
    """
    events = event(10, EventType.FEEDBACK_DISPLAYED)["event"]
    assert events.apply(lambda x: x["student_answer"] == []).any()
