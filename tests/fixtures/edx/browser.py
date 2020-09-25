"""
Broser event factory definitions
"""
import json
from urllib.parse import urlencode

import factory
from faker import Faker

from ralph.schemas.edx.browser import (
    BROWSER_EVENT_TYPE_FIELD,
    BROWSER_EVENT_VALID_AMOUNT,
    BROWSER_NAME_FIELD,
    BaseBrowserEventSchema,
    PageCloseBrowserEventSchema,
    ProblemCheckBrowserEventSchema,
    ProblemGradedBrowserEventSchema,
    ProblemResetBrowserEventSchema,
    ProblemSaveBrowserEventSchema,
    ProblemShowBrowserEventSchema,
    SeqGotoBrowserEventSchema,
    SeqNextBrowserEventSchema,
    SeqPrevBrowserEventSchema,
    TextbookPdfDisplayScaledBrowserEventSchema,
    TextbookPdfOutlineToggledBrowserEventSchema,
    TextbookPdfPageNavigatedBrowserEventSchema,
    TextbookPdfPageScrolledBrowserEventSchema,
    TextbookPdfThumbnailNavigatedBrowserEventSchema,
    TextbookPdfThumbnailsToggledBrowserEventSchema,
    TextbookPdfZoomButtonsChangedBrowserEventSchema,
    TextbookPdfZoomMenuChangedBrowserEventSchema,
)

from .base import _BaseContextFactory, _BaseEventFactory
from .mixins import JSONFactoryMixin, ObjFactoryMixin

FAKE = Faker()


class _BrowserEventFactory(_BaseEventFactory):
    """Represents a base browser event factory.
    This type of event is triggered on (XHR) POST/GET request to the
    `/event` URL
    """

    class Meta:  # pylint: disable=missing-class-docstring
        model = BaseBrowserEventSchema

    event_source = factory.Sequence(lambda n: "browser")
    session = factory.Sequence(lambda n: FAKE.md5(raw_output=False))
    page = factory.Sequence(lambda n: FAKE.url())
    event_type = factory.Sequence(
        lambda n: FAKE.random_element(BROWSER_EVENT_TYPE_FIELD)
    )

    # pylint: disable=no-member, unsubscriptable-object

    @factory.lazy_attribute
    def name(self):
        """Returns the name field which depends on the event_type field"""
        if self.event_type != "book":
            return self.event_type
        return FAKE.random_element(BROWSER_NAME_FIELD)

    @factory.lazy_attribute
    def context(self):
        """Returns the context field"""
        # pylint: disable=protected-access
        _BaseContextFactory._meta.exclude = ("course_user_tags",)
        if "org_id" not in self.context_args:
            self.context_args["org_id"] = FAKE.word()
        return _BaseContextFactory(path="/event", **self.context_args)

    @factory.lazy_attribute
    def event(self):
        """Returns the event field which depends on the name field"""
        course_key = self.context["course_id"][10:]
        if self.name == "page_close":
            return "{}"
        if self.name == "problem_show":
            problem = (
                f"block-v1:{course_key}+type@problem+block@{FAKE.md5(raw_output=False)}"
            )
            return json.dumps({"problem": problem})
        if self.name == "problem_check":
            return _BrowserEventFactory.get_urlencoded_str()
        if self.name in ["problem_graded", "problem_reset", "problem_save"]:
            # should return html at index 1 but faker don't support random
            # html gen - using faker.sentece() instead
            return [_BrowserEventFactory.get_urlencoded_str(), FAKE.sentence()]
        if self.name in ["seq_goto", "seq_next", "seq_prev"]:
            old = FAKE.random_int(0, 10)
            if self.name == "seq_goto":
                new = FAKE.random_int(0, old)
                new = old + new if FAKE.boolean() else old - new
            else:
                new = old + 1 if self.name == "seq_next" else old - 1
            return _BrowserEventFactory.get_seq_goto_event(
                self.context, old=old, new=new
            )
        return _BrowserEventFactory.handle_pdf_event(self, course_key)

    @staticmethod
    def get_urlencoded_str():
        """"returns at random a urlencoded string or empty string"""
        if FAKE.boolean(chance_of_getting_true=25):
            return ""
        params = {}
        problem_block_id = FAKE.md5(raw_output=False)
        multi_choice_brackets = "[]" if FAKE.boolean() else ""
        for i in range(2, FAKE.random_digit_not_null() + 2):
            params[
                f"input_{problem_block_id}_{i}_1{multi_choice_brackets}"
            ] = FAKE.random_element(
                elements=(
                    FAKE.random_int(),
                    FAKE.random_letter(),
                    FAKE.word(),
                    FAKE.sentence(),
                )
            )
        return urlencode(params)

    @staticmethod
    def get_seq_goto_event(context, old, new):
        """Returns the event field for the seq_goto event"""
        course_key = context["course_id"][10:]
        return json.dumps(
            {
                "new": new,
                "old": old,
                "id": f"block-v1:{course_key}+type@sequential+block@{FAKE.md5(raw_output=False)}",
            }
        )

    @staticmethod
    def handle_pdf_event(obj, course_key):
        """group logic for pdf related events"""
        event = {}
        if obj.name in [
            "textbook.pdf.outline.toggled",
            "textbook.pdf.thumbnail.navigated",
            "textbook.pdf.thumbnails.toggled",
            "textbook.pdf.page.navigated",
            "textbook.pdf.page.scrolled",
            "textbook.pdf.zoom.buttons.changed",
            "textbook.pdf.zoom.menu.changed",
            "textbook.pdf.display.scaled",
        ]:
            event["page"] = FAKE.random_int(0, 1000)
        if obj.name == "textbook.pdf.thumbnail.navigated":
            event["thumbnail_title"] = f"Page {event['page']}"
        if obj.name in [
            "textbook.pdf.zoom.buttons.changed",
            "textbook.pdf.page.scrolled",
        ]:
            scroll_or_zoom = (
                ["in", "out"] if obj.name[-7:] == "changed" else ["up", "down"]
            )
            event["direction"] = FAKE.random_element(scroll_or_zoom)
        if obj.name == "textbook.pdf.zoom.menu.changed":
            event["amount"] = FAKE.random_element(BROWSER_EVENT_VALID_AMOUNT)
        if obj.name == "textbook.pdf.display.scaled":
            event["amount"] = FAKE.pyfloat()
        event["chapter"] = f"/asset-v1:{course_key}+type@asset+block/{FAKE.slug()}.pdf"
        event["name"] = obj.name
        return json.dumps(event)


def _create_browser_factory(meta_model_class, event_type=None):
    """Returns a BrowserEventObjFactory and a BrowserEventStrFactory
    with the specified meta_model_class

    Exemple: for the `PageCloseBrowserEventSchema`
    it creates a PageCloseBrowserEventObjFactory
    """
    attributes = {"event_type": event_type} if event_type else {}
    custom_factory_obj = type(
        f"{meta_model_class.__name__[:-6]}ObjFactory)",
        (ObjFactoryMixin, _BrowserEventFactory),
        attributes,
    )
    custom_factory_str = type(
        f"{meta_model_class.__name__[:-6]}ObjFactory)",
        (JSONFactoryMixin, _BrowserEventFactory),
        attributes,
    )
    # pylint: disable=protected-access
    custom_factory_obj._meta.model = meta_model_class
    custom_factory_str._meta.model = meta_model_class
    return custom_factory_obj, custom_factory_str


# pylint: disable=invalid-name
# pylint complains that constant names should be capitalized
# but to be consistent with other classes, BaseBrowserEventObjFactory
# and others should be considered as `class definitions`

BaseBrowserEventObjFactory, BaseBrowserEventStrFactory = _create_browser_factory(
    BaseBrowserEventSchema
)

(
    PageCloseBrowserEventObjFactory,
    PageCloseBrowserEventStrFactory,
) = _create_browser_factory(PageCloseBrowserEventSchema, event_type="page_close")

(
    ProblemCheckBrowserEventObjFactory,
    ProblemCheckBrowserEventStrFactory,
) = _create_browser_factory(ProblemCheckBrowserEventSchema, event_type="problem_check")

(
    ProblemGradedBrowserEventObjFactory,
    ProblemGradedBrowserEventStrFactory,
) = _create_browser_factory(
    ProblemGradedBrowserEventSchema, event_type="problem_graded"
)

(
    ProblemResetBrowserEventObjFactory,
    ProblemResetBrowserEventStrFactory,
) = _create_browser_factory(ProblemResetBrowserEventSchema, event_type="problem_reset")

(
    ProblemSaveBrowserEventObjFactory,
    ProblemSaveBrowserEventStrFactory,
) = _create_browser_factory(ProblemSaveBrowserEventSchema, event_type="problem_save")

(
    ProblemShowBrowserEventObjFactory,
    ProblemShowBrowserEventStrFactory,
) = _create_browser_factory(ProblemShowBrowserEventSchema, event_type="problem_show")

SeqGotoBrowserEventObjFactory, SeqGotoBrowserEventStrFactory = _create_browser_factory(
    SeqGotoBrowserEventSchema, event_type="seq_goto"
)

SeqNextBrowserEventObjFactory, SeqNextBrowserEventStrFactory = _create_browser_factory(
    SeqNextBrowserEventSchema, event_type="seq_next"
)

SeqPrevBrowserEventObjFactory, SeqPrevBrowserEventStrFactory = _create_browser_factory(
    SeqPrevBrowserEventSchema, event_type="seq_prev"
)

(
    TextbookPdfDisplayScaledBrowserEventObjFactory,
    TextbookPdfDisplayScaledBrowserEventStrFactory,
) = _create_browser_factory(
    TextbookPdfDisplayScaledBrowserEventSchema,
    event_type="textbook.pdf.display.scaled",
)

(
    TextbookPdfOutlineToggledBrowserEventObjFactory,
    TextbookPdfOutlineToggledBrowserEventStrFactory,
) = _create_browser_factory(
    TextbookPdfOutlineToggledBrowserEventSchema,
    event_type="textbook.pdf.outline.toggled",
)

(
    TextbookPdfPageNavigatedBrowserEventObjFactory,
    TextbookPdfPageNavigatedBrowserEventStrFactory,
) = _create_browser_factory(
    TextbookPdfPageNavigatedBrowserEventSchema, event_type="textbook.pdf.page.navigated"
)

(
    TextbookPdfPageScrolledBrowserEventObjFactory,
    TextbookPdfPageScrolledBrowserEventStrFactory,
) = _create_browser_factory(
    TextbookPdfPageScrolledBrowserEventSchema, event_type="textbook.pdf.page.scrolled"
)

(
    TextbookPdfThumbnailNavigatedBrowserEventObjFactory,
    TextbookPdfThumbnailNavigatedBrowserEventStrFactory,
) = _create_browser_factory(
    TextbookPdfThumbnailNavigatedBrowserEventSchema,
    event_type="textbook.pdf.thumbnail.navigated",
)

(
    TextbookPdfThumbnailsToggledBrowserEventObjFactory,
    TextbookPdfThumbnailsToggledBrowserEventStrFactory,
) = _create_browser_factory(
    TextbookPdfThumbnailsToggledBrowserEventSchema,
    event_type="textbook.pdf.thumbnails.toggled",
)

(
    TextbookPdfZoomButtonsChangedBrowserEventObjFactory,
    TextbookPdfZoomButtonsChangedBrowserEventStrFactory,
) = _create_browser_factory(
    TextbookPdfZoomButtonsChangedBrowserEventSchema,
    event_type="textbook.pdf.zoom.buttons.changed",
)

(
    TextbookPdfZoomMenuChangedBrowserEventObjFactory,
    TextbookPdfZoomMenuChangedBrowserEventStrFactory,
) = _create_browser_factory(
    TextbookPdfZoomMenuChangedBrowserEventSchema,
    event_type="textbook.pdf.zoom.menu.changed",
)
