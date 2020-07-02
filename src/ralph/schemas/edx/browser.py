"""
Browser event schema definitions
"""
import json
import urllib.parse

from marshmallow import ValidationError, fields, validates_schema
from marshmallow.validate import URL, Equal, OneOf

from .base import BaseEventSchema

BROWSER_EVENT_TYPE_FIELD = [
    "page_close",
    "problem_show",
    "problem_check",
    "problem_graded",
    "problem_reset",
    "problem_save",
    "seq_goto",
    "seq_next",
    "seq_prev",
    "textbook.pdf.thumbnails.toggled",
    "textbook.pdf.thumbnail.navigated",
    "textbook.pdf.outline.toggled",
    "textbook.pdf.zoom.buttons.changed",
    "textbook.pdf.zoom.menu.changed",
    "textbook.pdf.page.scrolled",
    "textbook.pdf.page.navigated",
    "textbook.pdf.display.scaled",
    "book",
]

BROWSER_NAME_FIELD = [
    "textbook.pdf.page.loaded",
    "textbook.pdf.page.navigatednext",
    "textbook.pdf.search.executed",
    "textbook.pdf.search.highlight.toggled",
    "textbook.pdf.search.navigatednext",
    "textbook.pdf.searchcasesensitivity.toggled",
]


class BrowserEventSchema(BaseEventSchema):
    """Represents a common browser event.
    This type of event is triggered on (XHR) POST/GET request to the
    `/event` URL
    """

    # pylint: disable=no-self-use
    @validates_schema
    def validate_name(self, data, **kwargs):
        """the name field should be equal to the event_type
        in case event_type is not `book`
        """
        if data["event_type"] != "book" and data["event_type"] != data["name"]:
            raise ValidationError(
                "the name field should be equal to the event_type when event_type is not `book`"
            )
        if data["event_type"] == "book" and data["name"] not in BROWSER_NAME_FIELD:
            raise ValidationError("the name field is not one of the allowed values")

    # pylint: disable=no-self-use
    @validates_schema
    def validate_context_path(self, data, **kwargs):
        """check that the context.path is equal to `/event`"""
        if data["context"]["path"] != "/event":
            raise ValidationError("The event path field is not `/event`")

    # pylint: disable=no-self-use
    @validates_schema
    def validate_event_page_close(self, data, **kwargs):
        """check that event is empty dict when name is `page_close`"""
        if data["name"] == "page_close":
            if data["event"] != "{}":
                raise ValidationError("event should be {} when name is `page_close`")

    # pylint: disable=no-self-use
    @validates_schema
    def validate_event_problem_show(self, data, **kwargs):
        """check that event is a prasable json objet when name is `problem_show`"""
        if data["name"] == "problem_show":
            if data["context"]["org_id"] == "":
                raise ValidationError(
                    "event context.org_id should not be empty when name is problem_show"
                )
            try:
                event = json.loads(data["event"])
            except (json.JSONDecodeError, TypeError):
                raise ValidationError(
                    "event field should contain a parsable json string"
                )
            keys = list(event.keys())
            if len(keys) != 1 or "problem" not in keys:
                raise ValidationError(
                    "event field should contain only one key of name `problem`"
                )
            value = event["problem"]
            course_key = data["context"]["course_id"][10:]
            if value[:-32] != f"block-v1:{course_key}+type@problem+block@":
                raise ValidationError(
                    f"the event.problem value should start with "
                    f"block-v1:{course_key}+type@problem+block"
                )

    # pylint: disable=no-self-use
    @validates_schema
    def validate_event_problem_check(self, data, **kwargs):
        """check that event is a standard URL-encoded string or empty"""
        if data["name"] == "problem_check":
            if data["event"] != "":
                try:
                    urllib.parse.parse_qs(data["event"], strict_parsing=True)
                except (ValueError, AttributeError):
                    raise ValidationError(
                        "event value should be a valid URL-encoded string"
                    )

    # pylint: disable=no-self-use
    @validates_schema
    def validate_event_problem_graded_reset_save(self, data, **kwargs):
        """check that event is a list of lenght 2 and that the first
        value is a valid URL-encoded string or empty
        for event_types `problem_graded`, `problem_reset` and `problem_save`
        """
        if data["name"] in ["problem_graded", "problem_reset", "problem_save"]:
            if not isinstance(data["event"], list) or len(data["event"]) != 2:
                raise ValidationError("event value should be a list of length 2")
            if data["event"][0] != "":
                try:
                    urllib.parse.parse_qs(data["event"][0], strict_parsing=True)
                except (ValueError, AttributeError):
                    raise ValidationError(
                        "event first value in list should be a valid URL-encoded string"
                    )

    # pylint: disable=no-self-use
    @validates_schema
    def validate_event_seq_goto(self, data, **kwargs):
        """check that the event is a string containing a json object
        with 3 keys: `new`: integer, `old`: integer, `id`: string
        Same validation applies to `seq_next`, `seq_prev` names
        """
        if data["name"] in ["seq_goto", "seq_next", "seq_prev"]:
            try:
                event = json.loads(data["event"])
            except (json.JSONDecodeError, TypeError):
                raise ValidationError(
                    "event field should contain a parsable json string"
                )
            keys = list(event.keys())
            for key in ["new", "old", "id"]:
                if key not in keys:
                    raise ValidationError(
                        f"{key} key should be present in the json string"
                    )
            if len(keys) != 3:
                raise ValidationError("the event field should contain 3 keys")
            if not isinstance(event["new"], int) or not isinstance(event["old"], int):
                raise ValidationError(
                    "event.new and event.old should have integer as values"
                )
            course_key = data["context"]["course_id"][10:]
            if event["id"][:-32] != f"block-v1:{course_key}+type@sequential+block@":
                raise ValidationError(
                    f"the event.id value should start with "
                    f"block-v1:{course_key}+type@problem+block"
                )

    # pylint: disable=no-self-use
    @validates_schema
    def validate_event_seq_next_seq_prev(self, data, **kwargs):
        """check that the event is a string containing a json object
        with 3 keys: `new`: integer, `old`: integer, `id`: string
        and that `new` is equal to (`old` + 1) for seq_next
        (and the opposite) for seq_prev
        """
        if data["name"] in ["seq_next", "seq_prev"]:
            diff = 1
            if data["name"] == "seq_prev":
                diff = -1
            event = json.loads(data["event"])
            if event["old"] + diff != event["new"]:
                raise ValidationError(
                    f"event.old should be equal to (event.new {diff})"
                )

    # pylint: disable=no-self-use
    @validates_schema
    def validate_event_textbook_pdf(self, data, **kwargs):
        """check that the event is a string containing a json object
        with 3 keys: `name`: string, `page`: integer > 0, `chapter`: url
        and `name` should be equal to event `name`
        """
        if data["name"] in [
            "textbook.pdf.thumbnails.toggled",
            "textbook.pdf.outline.toggled",
            "textbook.pdf.page.navigated",
        ]:
            try:
                event = json.loads(data["event"])
            except (json.JSONDecodeError, TypeError):
                raise ValidationError(
                    "event field should contain a parsable json string"
                )
            keys = list(event.keys())
            for key in ["name", "page", "chapter"]:
                if key not in keys:
                    raise ValidationError(
                        f"{key} key should be present in the json string"
                    )
            if len(keys) != 3:
                raise ValidationError("the event field should contain 3 keys")
            if not isinstance(event["page"], int) or not event["page"] > 0:
                raise ValidationError("event.page should have integer as value > 0")
            if data["name"] != event["name"]:
                raise ValidationError(
                    "event.name should be equal to the name of the browser event"
                )
            URL(relative=True)(event["chapter"])
            course_key = data["context"]["course_id"][10:]
            chapter_begin = f"/asset-v1:{course_key}+type@asset+block/"
            if event["chapter"][: len(chapter_begin)] != chapter_begin:
                raise ValidationError(
                    f"the event.chapter should begin with {chapter_begin}"
                )
            if event["chapter"][-4:] != ".pdf":
                raise ValidationError("the event.chapter should end with .pdf")

    # pylint: disable=no-self-argument, no-self-use
    def validate_session(value):
        """"check session field empty or 32 chars long"""
        if value != "" and len(value) != 32:
            raise ValidationError("session should be empty or 32 chars long (md5 key)")

    event_source = fields.Str(
        required=True,
        validate=Equal(
            comparable="browser", error='The event event_source field is not "browser"'
        ),
    )
    event_type = fields.Str(
        required=True,
        validate=OneOf(
            choices=BROWSER_EVENT_TYPE_FIELD,
            error="The event name field value is not one of the valid values",
        ),
    )
    name = fields.Str(required=True)
    page = fields.Url(required=True, relative=True)
    session = fields.Str(required=True, validate=validate_session)
    event = fields.Field(required=True)
