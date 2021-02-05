"""Base event factory definitions"""

import json
from datetime import timezone

import factory
from faker import Faker

from ralph.schemas.edx.base import (
    BaseContextSchema,
    BaseEventSchema,
    ContextModuleSchema,
    ContextSchema,
)

# pylint: disable=no-self-argument, no-self-use, no-member
# pylint: disable=comparison-with-callable, unsubscriptable-object

FAKE = Faker()


class BaseFactory(factory.Factory):
    """Base Factory inherited by all event related factories"""

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our custom call."""

        schema = model_class()
        kwargs_json = json.dumps(kwargs)
        event = schema.loads(kwargs_json)
        return schema.dump(event)


class BaseContextFactory(BaseFactory):
    """Base context factory inherited by all context factories"""

    class Meta:  # pylint: disable=missing-class-docstring
        model = BaseContextSchema

    course_user_tags = factory.Sequence(lambda n: {FAKE.word(): FAKE.word()})
    path = factory.Sequence(lambda n: f"/{FAKE.uri_path()}")

    @factory.sequence
    def user_id(number):
        """Return the user_id which can be a number, empty or None"""

        return FAKE.random_element(elements=(FAKE.random_int(), "", None))

    @factory.sequence
    def org_id(number):
        """Return the org_id which depends on course_user_tags"""

        if "course_user_tags" in BaseContextFactory._meta.exclude:
            return ""
        return FAKE.word()

    @factory.lazy_attribute
    def course_id(self):
        """Return the course_id which contains org_id"""

        if self.org_id == "":
            return ""
        return f"course-v1:{self.org_id}+{FAKE.word()}+{FAKE.word()}"


class ContextModuleFactory(BaseFactory):
    """Represents the context module field"""

    class Meta:  # pylint: disable=missing-class-docstring
        model = ContextModuleSchema

    class Params:  # pylint: disable=missing-class-docstring
        course_id = ""

    @factory.lazy_attribute
    def usage_key(self):
        """Return the usage key which depends on the course_id"""

        block_id = FAKE.md5(raw_output=False)
        # pylint: disable=no-member
        return f"block-v1:{self.course_id[10:]}+type@problem+block@{block_id}"

    display_name = factory.Sequence(lambda n: FAKE.sentence())


class ContextFactory(BaseContextFactory):
    """Context with module field. Present in CAPA problems related
    events.
    """

    class Meta:  # pylint: disable=missing-class-docstring
        model = ContextSchema
        exclude = ()

    class Params:  # pylint: disable=missing-class-docstring
        path_tail = ""

    user_id = factory.Sequence(lambda n: FAKE.random_int())
    org_id = factory.Sequence(lambda n: FAKE.word())
    module = factory.LazyAttribute(
        lambda o: ContextModuleFactory(course_id=o.course_id)
    )

    @factory.lazy_attribute
    def path(self):
        """Return the path field which depends on the context module"""

        usage_key = self.module["usage_key"][-32:]
        return (
            f"/courses/course-v1:{self.course_id[10:]}"
            f"/xblock/block-v1:{self.course_id[10:]}+type@problem+block"
            f"@{usage_key}/handler/{self.path_tail}"
        )


class BaseEventFactory(BaseFactory):
    """Base Event factory inherited by all event factories"""

    class Meta:  # pylint: disable=missing-class-docstring
        model = BaseEventSchema

    class Params:  # pylint: disable=missing-class-docstring
        context_args = {}

    @factory.sequence
    def username(number):
        """Return the user name which may me empty"""

        if FAKE.boolean():
            return ""
        return FAKE.profile().get("username")

    ip = factory.Sequence(lambda n: FAKE.ipv4_public())
    agent = factory.Sequence(lambda n: FAKE.user_agent())
    host = factory.Sequence(lambda n: FAKE.hostname())
    referer = factory.Sequence(lambda n: FAKE.url())
    accept_language = factory.Sequence(lambda n: FAKE.locale())
    event_source = factory.Sequence(lambda n: "server")
    time = factory.Sequence(lambda n: FAKE.iso8601(tzinfo=timezone.utc))
    page = factory.Sequence(lambda n: None)

    @factory.lazy_attribute
    def context(self):
        """Return the context field"""

        exclude_course_user_tags = FAKE.boolean()
        if "course_user_tags" in self.context_args:
            exclude_course_user_tags = False
        # pylint: disable=protected-access
        BaseContextFactory._meta.exclude = ()
        if exclude_course_user_tags:
            # pylint: disable=protected-access
            BaseContextFactory._meta.exclude = ("course_user_tags",)
        return BaseContextFactory(**self.context_args)
