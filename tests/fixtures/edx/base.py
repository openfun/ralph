"""Base event factory definitions"""

from datetime import timezone

from factory import Factory, LazyAttribute, SubFactory
from faker import Faker

from ralph.models.edx.base import BaseContextModel, BaseEventModel

Faker.seed(1)
FAKE = Faker()


class BaseContextFactory(Factory):
    """Base context factory inherited by all context factories."""

    class Meta:  # pylint: disable=missing-class-docstring
        model = BaseContextModel

    course_user_tags = FAKE.pydict(value_types=str)
    path = f"/{FAKE.uri_path()}"
    user_id = FAKE.random_element(elements=(FAKE.random_int(), "", None))
    org_id = FAKE.word()
    course_id = LazyAttribute(
        lambda self: f"course-v1:{self.org_id}+{FAKE.word()}+{FAKE.word()}"
    )


class BaseEventFactory(Factory):
    """Base event factory inherited by all event factories."""

    class Meta:  # pylint: disable=missing-class-docstring
        model = BaseEventModel

    username = FAKE.user_name() if FAKE.boolean() else ""
    ip = FAKE.ipv4_public()
    agent = FAKE.user_agent()
    host = FAKE.hostname()
    referer = FAKE.url()
    accept_language = FAKE.locale()
    event_source = "server"
    context = SubFactory(BaseContextFactory)
    time = FAKE.iso8601(tzinfo=timezone.utc)
    page = None
