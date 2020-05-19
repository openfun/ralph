"""
Server event fixture definition
"""

from faker import Faker

from .base import BaseEvent, EventFieldProperties, FreeEventField
from .context import BaseContext, TriggeredContext

# Faker.seed(0)
FAKE = Faker()


class BaseServerEvent(BaseEvent):
    """Represents a common server event.
    This type of event is triggered on almost every request to the LMS.
    It lets us know that an Agent has launched a paritcular web page
    or made an ajax request.
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, *args, **kwargs):
        super(BaseServerEvent, self).__init__(*args, **kwargs)
        emptiable_str_property = EventFieldProperties(emptiable_str=True)
        self.username = FreeEventField(
            FAKE.user_name, properties=emptiable_str_property
        )
        self.ip = FreeEventField(  # pylint: disable=invalid-name
            FAKE.ipv4_public, properties=emptiable_str_property
        )
        self.agent = FreeEventField(FAKE.user_agent, properties=emptiable_str_property)
        self.host = FAKE.hostname()
        self.referer = FreeEventField(FAKE.url, properties=emptiable_str_property)
        self.accept_language = FreeEventField(
            FAKE.locale, properties=emptiable_str_property
        )
        self.event_source = "server"
        self.time = FAKE.iso8601()
        self.page = None
        self.context = BaseContext(*args, **kwargs.get("context", {}))
        self.event = self.get_event()
        self.event_type = self.context.path
        if "is_anonymous" in kwargs:
            if kwargs["is_anonymous"]:
                self.username = ""
                self.context.user_id = None
                self.context.course_user_tags = FreeEventField(lambda: "", removed=True)
            else:
                self.username = FAKE.user_name()
                self.context.user_id = FAKE.random_int()

    @staticmethod
    def get_event():
        """ returns randomly empty/filled POST/GET value"""
        empty = '{"POST": {}, "GET": {}}'
        post = (
            '{"POST": {"input_e8bc718966e9441abc3ccf1a6429ee8b_2_1": ["choice_2"]},'
            ' "GET": {}}'
        )
        get = '{"POST": {}, "GET": {"rpp": ["50"], "page": ["1"]}}'
        return FAKE.random_element([empty, post, get])

    @staticmethod
    def get_block_id(context, prefix, block_type, suffix=None):
        """Returns a random problem block usage locator"""
        if isinstance(context, BaseEvent):
            course_key = context.course_id[10:]
        else:
            course_key = context["course_id"][
                10:
            ]  # pylint: disable=unsubscriptable-object
        suffix = suffix if suffix else "@" + FAKE.md5(raw_output=False)
        return "{}:{}+type@{}+block{}".format(prefix, course_key, block_type, suffix)

    @staticmethod
    def get_module_id(context):
        """Returns the module_id wich depends on the usage_key"""
        return BaseServerEvent.get_block_id(
            context, "block-v1", "problem", "@" + context["module"]["usage_key"][-32:]
        )


class BaseTriggeredEvent(BaseServerEvent):
    """Represents a special server event.
    For some specific page requests we write additional logs on top of
    the usual server logs.
    They are handled after the middleware layer.
    """

    def __init__(self, *args, **kwargs):
        super(BaseTriggeredEvent, self).__init__(*args, **kwargs)
        self.username = FAKE.user_name()
        self.page = "x_module"
        self.event_type = kwargs.get(
            "sub_type", "edx.problem.hint.demandhint_displayed"
        )
        self.context = TriggeredContext(*args, **kwargs.get("context", {}))
