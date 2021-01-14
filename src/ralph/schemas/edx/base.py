"""Base event schema definitions"""
from ipaddress import IPv4Address

from marshmallow import Schema, ValidationError, validates, validates_schema
from marshmallow.fields import DateTime, Dict, Field, Nested, Str, Url
from marshmallow.validate import URL, Equal

# pylint: disable=no-self-use, unused-argument


class BaseContextSchema(Schema):
    """Represents the Base Context inherited by all event contexts"""

    course_user_tags = Dict(keys=Str(), values=Str())
    user_id = Field(required=True, allow_none=True)
    org_id = Str(required=True)
    course_id = Str(required=True)
    path = Url(required=True, relative=True)

    @validates("user_id")
    def validate_user_id(self, value):
        """"Check user_id field is None, an empty string or an integer"""
        if value is None or value == "" or isinstance(value, int):
            return
        raise ValidationError("user_id should be None, an empty string or an integer")

    @validates_schema
    def validate_course_id(self, data, **kwargs):
        """The course_id should be equal to
        "course-v1:{org_id}+{any_string}+{any_string}"
        or be an empty string if org_id is an empty string
        """
        org_id = data["org_id"]
        course_id = data["course_id"]
        if not org_id and course_id:
            raise ValidationError("course_id should be empty if org_id is empty")
        if org_id and not course_id:
            raise ValidationError("org_id should be empty if course_id is empty")
        if not org_id:
            return
        if not course_id.startswith("course-v1:"):
            raise ValidationError("course_id should starts with 'course-v1'")
        try:
            organization, course, session = course_id.replace("course-v1:", "").split(
                "+"
            )
        except ValueError as value_error:
            raise ValidationError(
                "course_id should contain an organization ID, "
                "a course name and session separated by a +"
            ) from value_error
        if organization != data["org_id"]:
            raise ValidationError(
                "organization ID in the course ID does not match the event organization ID"
            )
        if len(course) == 0 or len(session) == 0:
            raise ValidationError("course and session should not be empty")


class ContextModuleSchema(Schema):
    """Represents the context module field"""

    usage_key = Str(required=True)
    display_name = Str(required=True)


class ContextSchema(BaseContextSchema):
    """Context with module field. Present in CAPA problems related
    events.
    """

    module = Nested(ContextModuleSchema(), required=True)

    @validates_schema
    def validate_path(self, data, **kwargs):
        """Path should start with:
        "/courses/{course_id}/xblock/block-v1:{course_id[10:]}
        +type@problem+block@{usage_key}/handler/"
        """

        path = data["path"]
        valid_path = (
            f"/courses/"
            f"{data['course_id']}"
            f"/xblock/"
            f"{data['module']['usage_key']}/"
            f"handler/"
        )
        if not path.startswith(valid_path):
            raise ValidationError(
                f"path should start with: "
                f"{valid_path} "
                f"but {path[:len(valid_path)]} does not match!"
            )


class BaseEventSchema(Schema):
    """Represents the Base Event Schema all events inherit from.
    Does not define event and event_type fields
    """

    username = Str(required=True)
    ip = Field(required=True)
    agent = Str(required=True)
    host = Str(required=True)
    referer = Str(required=True)
    accept_language = Str(required=True)
    event_source = Str(
        required=True,
        validate=Equal(
            comparable="server", error="The event event_source field is not `server`"
        ),
    )
    context = Nested(BaseContextSchema(), required=True)
    time = DateTime(format="iso", required=True)
    page = Str(
        required=True,
        allow_none=True,
        validate=Equal(comparable=None, error="The event page field is not None"),
    )

    @validates("username")
    def validate_username(self, value):
        """"Check username field empty or 2-30 chars long"""

        if len(value) == 1 or len(value) > 30:
            raise ValidationError(
                "username should be empty or between 2 and 30 characters long"
            )

    @validates("referer")
    def validate_referer(self, value):
        """Check referer field empty or a valid URL"""

        if value != "":
            URL(relative=True)(value)

    @validates("ip")
    def validate_ip(self, value):
        """Check the IP address is empty or a valid IPv4 address."""

        if value != "":
            try:
                IPv4Address(value)
            except ValueError as err:
                raise ValidationError("Invalid IPv4 Address") from err

    @staticmethod
    def get_course_key(data):
        """Return the course key: organization+course+session"""

        return data["context"]["course_id"][10:]

    @staticmethod
    def get_block_id(data, prefix="block-v1", block_type="problem", suffix="@"):
        """Return the block id: {prefix}:{course_key}+type@{block_type}+block{suffix}"""

        return f"{prefix}:{BaseEventSchema.get_course_key(data)}+type@{block_type}+block{suffix}"
