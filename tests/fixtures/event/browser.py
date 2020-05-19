"""
Browser event fixture definition
"""
import json
from urllib.parse import urlencode

from faker import Faker

from .base import EventFieldProperties, FreeEventField, TiedEventField
from .server import BaseServerEvent

# Faker.seed(0)
FAKE = Faker()


class BrowserEvent(BaseServerEvent):
    """Represents a Browser event.
    This type of event is triggered by the LMS front-end sending an
    ajax request to the '/event' route.
    It lets us know that an Agent has closed a page, interracted with
    an assessment, read a page of a manual, and many more.
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, *args, **kwargs):
        super(BrowserEvent, self).__init__(*args, **kwargs)
        self.event_source = "browser"
        self.page = FAKE.url()
        self.session = FreeEventField(
            FAKE.md5,
            properties=EventFieldProperties(emptiable_str=True),
            raw_output=False,
        )
        self.context.path = "/event"
        self.context.course_user_tags = FreeEventField(lambda: "", removed=True)
        self.event_type = kwargs.get("sub_type", "page_close")
        self.name = self.event_type
        if self.event_type == "book":
            self.name = self.kwargs.get("book_event_type", "textbook.pdf.page.loaded")
        self.handle_common_sub_types()
        self.handle_pdf_sub_types()

    def handle_common_sub_types(self):
        """group all common sub_type conditions in a function"""
        if self.name == "page_close":
            self.event = "{}"
        if self.name == "problem_show":
            self.context.org_id = FAKE.word()
            self.event = TiedEventField(
                self.get_problem_show_event, dependency="context"
            )
        if self.name == "problem_check":
            self.event = self.get_urlencoded_str()
        if self.name in ["problem_graded", "problem_reset", "problem_save"]:
            # should return html at index 1 but faker don't support random
            # html gen - using faker.sentece() instead
            self.event = [self.get_urlencoded_str(), FAKE.sentence()]
        if self.name == "seq_goto":
            old = FAKE.random_int(0, 10)
            new = FAKE.random_int(0, old)
            new = old + new if FAKE.boolean() else old - new
            self.event = TiedEventField(
                self.get_seq_goto_event, dependency="context", old=old, new=new
            )
        if self.name in ["seq_next", "seq_prev"]:
            old = FAKE.random_int(0, 10)
            new = old + 1 if self.name == "seq_next" else old - 1
            self.event = TiedEventField(
                self.get_seq_goto_event, dependency="context", old=old, new=new
            )

    def handle_pdf_sub_types(self):
        """group all pdf sub_type conditions in a function"""
        if self.name in [
            "textbook.pdf.thumbnails.toggled",
            "textbook.pdf.outline.toggled",
            "textbook.pdf.page.navigated",
        ]:
            event_json = {"page": FAKE.random_int(0, 1000)}
        if self.name == "textbook.pdf.thumbnail.navigated":
            page = FAKE.random_int(0, 1000)
            event_json = {"thumbnail_title": "Page {}".format(page), "page": page}
        if self.name in [
            "textbook.pdf.zoom.buttons.changed",
            "textbook.pdf.page.scrolled",
        ]:
            page = FAKE.random_int(0, 1000)
            scroll_or_zoom = (
                ["in", "out"] if self.name[-7:] == "changed" else ["up", "down"]
            )
            direction = FAKE.random_element(scroll_or_zoom)
            event_json = {"direction": direction, "page": page}
        if self.name == "textbook.pdf.zoom.menu.changed":
            page = FAKE.random_int(0, 1000)
            amaunt = FAKE.random_element(
                [
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
            )
            event_json = {"amaunt": amaunt, "page": page}
        if self.name == "textbook.pdf.display.scaled":
            page = FAKE.random_int(0, 1000)
            amaunt = FAKE.pyfloat(right_digits=2, min_value=-4, max_value=4)
            event_json = {"amaunt": amaunt, "page": page}
        if self.name == "textbook.pdf.page.loaded":
            old = FAKE.random_int(0, 1000)
            new = FAKE.random_int(0, 1000)
            event_json = {"type": "gotopage", "old": old, "new": new}
        if self.name == "textbook.pdf.page.navigatednext":
            new = FAKE.random_int(0, 1000)
            _type = FAKE.random_element(["prevpage", "nextpage"])
            event_json = {"type": _type, "new": new}
        if self.name in [
            "textbook.pdf.search.executed",
            "textbook.pdf.search.highlight.toggled",
            "textbook.pdf.search.navigatednext",
            "textbook.pdf.searchcasesensitivity.toggled",
        ]:
            status = FreeEventField(
                lambda: "Phrase not found",
                properties=EventFieldProperties(emptiable_str=True),
            ).get(*self.args)
            query = FreeEventField(
                FAKE.word, properties=EventFieldProperties(emptiable_str=True)
            ).get(*self.args)
            event_json = {
                "caseSensitive": FAKE.boolean(),
                "highlightAll": FAKE.boolean(),
                "page": FAKE.random_int(0, 1000),
                "query": query,
                "status": status,
            }
        if self.name == "textbook.pdf.search.navigatednext":
            event_json["findprevious"] = FAKE.boolean()
        if self.name[:12] == "textbook.pdf" or self.event_type == "book":
            self.event = TiedEventField(
                self.add_chapter_and_name,
                dependency="context",
                event_json=event_json,
                name=self.name,
            )

    @staticmethod
    def get_urlencoded_str():
        """"returns at random a urlencoded string or empty string"""
        params = {}
        problem_block_id = FAKE.md5(raw_output=False)
        multi_choice_brackets = "[]" if FAKE.boolean() else ""
        for i in range(2, FAKE.random_digit_not_null() + 2):
            params[
                "input_%s_%i_1%s" % (problem_block_id, i, multi_choice_brackets)
            ] = FAKE.random_element(
                elements=(
                    FAKE.random_int(),
                    FAKE.random_letter(),
                    FAKE.word(),
                    FAKE.sentence(),
                )
            )
        return urlencode(params) if FAKE.boolean(chance_of_getting_true=75) else ""

    @staticmethod
    def get_problem_show_event(context):
        """Returns the event field for the problem_show event"""
        return json.dumps(
            {
                "problem": BrowserEvent.get_block_id(
                    context, prefix="block-v1", block_type="problem"
                )
            }
        )

    @staticmethod
    def get_seq_goto_event(context, old, new):
        """Returns the event field for the seq_goto event"""
        return json.dumps(
            {
                "new": new,
                "old": old,
                "id": BrowserEvent.get_block_id(
                    context, prefix="block-v1", block_type="sequential"
                ),
            }
        )

    @staticmethod
    def add_chapter_and_name(context, event_json, name):
        """Adds chapter and page to event_json and its json string"""
        event_json["chapter"] = BrowserEvent.get_block_id(
            context, "/asset-v1", "asset", "/" + FAKE.slug() + ".pdf"
        )
        event_json["name"] = name
        return json.dumps(event_json)
