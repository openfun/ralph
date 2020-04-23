"""
Logs format pytest fixtures.
"""
import json
import logging
from secrets import token_hex
from tempfile import NamedTemporaryFile
from urllib.parse import urlencode

import factory
import pandas as pd
import pytest
from djehouty.libgelf.formatters import GELFFormatter
from faker import Faker

FAKE = Faker()


@pytest.fixture
def gelf_logger():
    """Generate a GELF logger to generate wrapped tracking log fixtures."""

    handler = logging.StreamHandler(NamedTemporaryFile(mode="w+", delete=False))
    handler.setLevel(logging.INFO)
    handler.setFormatter(GELFFormatter(null_character=False))

    # Generate a unique logger per test function to avoid stacking handlers on
    # the same one
    logger = logging.getLogger(f"test_logger_{token_hex(8)}")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger


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


class EventContext(factory.Factory):
    """Returns the common context dict all types of events are supposed to have"""

    class Meta:  # pylint: disable=missing-class-docstring
        model = dict

    course_user_tags = {}
    user_id = factory.Sequence(lambda n: FAKE.random_digit_or_empty())
    org_id = factory.Sequence(lambda n: FAKE.word())
    course_id = factory.Sequence(
        lambda n: "course-v1:%s+%s+%s" % (FAKE.word(), FAKE.word(), FAKE.word())
    )
    path = factory.Sequence(lambda n: FAKE.uri_path())


class ServerEvent(factory.Factory):
    """Reruns a DataFrame representing a server event.
    This type of event is triggered on almost every request to the LMS.
    It lets us know that an Agent has launched a paritcular web page
    or made an ajax request.
    """

    class Meta:  # pylint: disable=missing-class-docstring
        model = dict

    username = factory.Sequence(lambda n: FAKE.profile().get("username"))
    # event_type = factory.Sequence(lambda n: FAKE.uri_path())
    ip = factory.Sequence(lambda n: FAKE.ipv4_public())
    agent = factory.Sequence(lambda n: FAKE.user_agent())
    host = factory.Sequence(lambda n: FAKE.hostname())
    referer = factory.Sequence(lambda n: FAKE.url())
    accept_language = factory.Sequence(lambda n: FAKE.locale())
    event = '{"POST": {}, "GET": {}}'
    event_source = "server"
    context = factory.Sequence(lambda n: EventContext())
    time = factory.Sequence(lambda n: FAKE.iso8601())
    page = None

    @factory.lazy_attribute
    def event_type(self):
        """"event_type and context[path] share the same URI"""
        return self.context["path"]  # pylint: disable=E1136  # pylint/issues/3139

    class Params:  # pylint: disable=missing-class-docstring
        sub_type = "default"


class BrowserEvent(ServerEvent):
    """Reruns a DataFrame representing a server event.
    This type of event is triggered by the LMS front-end sending an
    ajax request to the '/event' route.
    It lets us know that an Agent has closed a page, interracted with
    an assessment, read a page of a manual, and many more.
    """

    event_source = "browser"
    page = factory.Sequence(lambda n: FAKE.url())
    session = factory.Sequence(lambda n: FAKE.md5(raw_output=False))

    @factory.sequence
    def context(self):  # pylint: disable=no-self-use
        """setup the common event context and update the path value"""
        context = EventContext()
        context["path"] = "/event"  # pylint: disable=unsupported-assignment-operation
        return context

    @factory.lazy_attribute
    def event_type(self):
        """the event_type is defined by sub_type of the event"""
        return self.sub_type  # pylint: disable=no-member

    @factory.lazy_attribute
    def name(self):
        """the name is defined by the event_type of the event"""
        return self.sub_type  # pylint: disable=no-member

    @factory.lazy_attribute
    def event(self):
        """the event attribute depends on the sub_type of the browser
        event. """
        if self.sub_type == "page_close":  # pylint: disable=no-member
            return "{}"
        if self.sub_type == "problem_show":  # pylint: disable=no-member
            ctxt = self.context["course_id"]  # pylint: disable=unsubscriptable-object
            course_key = ctxt[10:]
            return json.dumps(
                {
                    "problem": "block-v1:{}+type@problem+block@{}".format(
                        course_key, FAKE.md5(raw_output=False)
                    )
                }
            )
        if self.sub_type == "problem_check":  # pylint: disable=no-member
            return get_urlencoded_str()
        if self.sub_type == "problem_graded":  # pylint: disable=no-member
            # should return html at index 1 but faker don't support random html gen
            # using faker.sentece() instead
            return [get_urlencoded_str(), FAKE.sentence()]
        return "{}"

    class Params:  # pylint: disable=missing-class-docstring
        sub_type = "default"


EVENT_TYPES = {
    "server": {"obj": ServerEvent, "sub_type": [""], "default_sub_type": ""},
    "browser": {
        "obj": BrowserEvent,
        "sub_type": ["page_close", "problem_show", "problem_check", "problem_graded"],
        "default_sub_type": "page_close",
    },
}


@pytest.fixture
def event():
    """Returns an event generator that generates size number of events
    of the given event_type and given event_sub_type"""

    def _event(size, event_type="server", sub_type="default"):
        selected_event_type = EVENT_TYPES.get(event_type, EVENT_TYPES["server"])
        if sub_type in selected_event_type["sub_type"]:
            selected_event_sub_type = sub_type
        else:
            selected_event_sub_type = selected_event_type["default_sub_type"]
        return pd.DataFrame(
            selected_event_type["obj"].build_batch(
                size, sub_type=selected_event_sub_type
            )
        )

    return _event
