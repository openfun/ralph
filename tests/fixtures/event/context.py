"""
Context event field fixture definition
"""

from faker import Faker

from .base import BaseEvent, FreeEventField, TiedEventField

# Faker.seed(0)
FAKE = Faker()


class BaseContext(BaseEvent):
    """Represents the common event context"""

    def __init__(self, *args, **kwargs):
        super(BaseContext, self).__init__(*args, **kwargs)
        self.user_id = FreeEventField(
            FAKE.random_int, emptiable_str=True, nullable=True
        )
        self.org_id = FreeEventField(FAKE.word, emptiable_str=True)
        self.course_id = TiedEventField(
            self.get_course_id, dependency=["context", "org_id"]
        )
        self.path = FAKE.uri_path()
        self.course_user_tags = FreeEventField(
            lambda: {FAKE.word(): FAKE.word()}, optional=True, emptiable_dict=True
        )

    @staticmethod
    def get_course_id(org_id):
        """returns the course_id field """
        if org_id:
            return "course-v1:%s+%s+%s" % (org_id, FAKE.word(), FAKE.word())
        return ""


class TriggeredContextModule(BaseEvent):
    """Represents the module field for Triggered Server Events Context"""

    def __init__(self, *args, **kwargs):
        super(TriggeredContextModule, self).__init__(*args, **kwargs)
        self.usage_key = TiedEventField(
            self.get_usage_key, dependency=["context", "course_id"]
        )
        self.display_name = FreeEventField(FAKE.sentence, emptiable_str=True)

    @staticmethod
    def get_usage_key(course_id):
        """Returns the usage key which depends on the course_id"""
        block_id = FAKE.md5(raw_output=False)
        return "block-v1:{}+type@problem+block@{}".format(course_id[10:], block_id)


class TriggeredContext(BaseContext):
    """Represents the common context for Triggered Server Events"""

    def __init__(self, *args, **kwargs):
        super(TriggeredContext, self).__init__(*args, **kwargs)
        self.user_id = FAKE.random_int()
        self.org_id = FAKE.word()
        self.course_id = "course-v1:%s+%s+%s" % (self.org_id, FAKE.word(), FAKE.word())
        self.module = TriggeredContextModule(*args, **kwargs.get("module", {}))
        self.path = TiedEventField(
            self.get_path, dependency=["context", "module", "usage_key"]
        )

    def get_path(self, usage_key):
        """Returns the path field which depends on the context module"""
        return (
            "/courses/course-v1:{}"
            "/xblock/block-v1:{}+type@problem+block@{}/handler/xmodule_handler"
        ).format(self.course_id[10:], self.course_id[10:], usage_key[-32:])
