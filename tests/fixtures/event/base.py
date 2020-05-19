"""
Base event factory definitions
"""
import factory
from faker import Faker

from ralph.schemas.edx.base import (
    BaseContextSchema,
    BaseEventSchema,
    ContextModuleSchema,
    ContextSchema,
)

from .mixins import JSONFactoryMixin, ObjFactoryMixin

FAKE = Faker()


class _BaseContextFactory(ObjFactoryMixin, factory.Factory):
    """Base Context factory inherited by all context factories"""

    class Meta:  # pylint: disable=missing-class-docstring
        model = BaseContextSchema

    course_user_tags = factory.Sequence(lambda n: {FAKE.word(): FAKE.word()})
    path = factory.Sequence(lambda n: f"/{FAKE.uri_path()}")

    # pylint: disable=no-self-argument, no-self-use
    @factory.sequence
    def user_id(number):
        """Returns the user_id which can be a number, empty or None"""
        return FAKE.random_element(elements=(FAKE.random_int(), "", None))

    # pylint: disable=no-self-argument, no-self-use
    @factory.sequence
    def org_id(number):
        """returns the org_id which depends on course_user_tags"""
        if "course_user_tags" in _BaseContextFactory._meta.exclude:
            return ""
        return FAKE.word()

    # pylint: disable=comparison-with-callable
    @factory.lazy_attribute
    def course_id(self):
        """returns the course_id which contains org_id"""
        if self.org_id == "":
            return ""
        return f"course-v1:{self.org_id}+{FAKE.word()}+{FAKE.word()}"


class _ContextModuleFactory(ObjFactoryMixin, factory.Factory):
    """Represents the context module field"""

    class Meta:  # pylint: disable=missing-class-docstring
        model = ContextModuleSchema

    class Params:  # pylint: disable=missing-class-docstring
        course_id = ""

    @factory.lazy_attribute
    def usage_key(self):
        """Returns the usage key which depends on the course_id"""
        block_id = FAKE.md5(raw_output=False)
        # pylint: disable=no-member
        return f"block-v1:{self.course_id[10:]}+type@problem+block@{block_id}"

    display_name = factory.Sequence(lambda n: FAKE.sentence())


class _ContextFactory(_BaseContextFactory):
    """Context with module field. Present in Capa problems related
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
        lambda o: _ContextModuleFactory(course_id=o.course_id)
    )

    # pylint: disable=unsubscriptable-object, no-member
    @factory.lazy_attribute
    def path(self):
        """Returns the path field which depends on the context module"""
        usage_key = self.module["usage_key"][-32:]
        return (
            f"/courses/course-v1:{self.course_id[10:]}"
            f"/xblock/block-v1:{self.course_id[10:]}+type@problem+block"
            f"@{usage_key}/handler/xmodule_handler{self.path_tail}"
        )


class _BaseEventFactory(factory.Factory):
    """Base Event factory inherited by all event factories"""

    class Meta:  # pylint: disable=missing-class-docstring
        model = BaseEventSchema

    class Params:  # pylint: disable=missing-class-docstring
        context_args = {}

    # pylint: disable=no-self-argument, no-self-use
    @factory.sequence
    def username(number):
        """Returns the user name which may me empty"""
        if FAKE.boolean():
            return ""
        return FAKE.profile().get("username")

    ip = factory.Sequence(lambda n: FAKE.ipv4_public())
    agent = factory.Sequence(lambda n: FAKE.user_agent())
    host = factory.Sequence(lambda n: FAKE.hostname())
    referer = factory.Sequence(lambda n: FAKE.url())
    accept_language = factory.Sequence(lambda n: FAKE.locale())
    event_source = factory.Sequence(lambda n: "server")
    time = factory.Sequence(lambda n: FAKE.iso8601())
    page = factory.Sequence(lambda n: None)

    # pylint: disable=no-member
    @factory.lazy_attribute
    def context(self):
        """Returns the context field"""
        exclude_course_user_tags = FAKE.boolean()
        # pylint: disable=protected-access
        _BaseContextFactory._meta.exclude = ()
        if exclude_course_user_tags:
            # pylint: disable=protected-access
            _BaseContextFactory._meta.exclude = ("course_user_tags",)
        return _BaseContextFactory(**self.context_args)


class BaseEventStrFactory(JSONFactoryMixin, _BaseEventFactory):
    """ Creates JSON Serialized model of the factory data """


class BaseEventObjFactory(ObjFactoryMixin, _BaseEventFactory):
    """ Creates Deserialized model of the factory data """
