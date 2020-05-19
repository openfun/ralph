"""
Base event schema definitions
"""
import re
from ipaddress import IPv4Address

from marshmallow import Schema, ValidationError, fields, validates_schema
from marshmallow.validate import URL, Equal


class BaseContextSchema(Schema):
    """Represents the Base Context inherited by all event contexts"""

    # pylint: disable=no-self-argument, no-self-use
    def validate_user_id(value):
        """"check user_id field empty or None or an Integer"""
        if value is not None and value != "" and not isinstance(value, int):
            raise ValidationError(
                "user_id should be None or empty string or an Integer"
            )

    course_user_tags = fields.Dict(keys=fields.Str(), values=fields.Str())
    user_id = fields.Field(required=True, allow_none=True, validate=validate_user_id)
    org_id = fields.Str(required=True)
    course_id = fields.Str(required=True)
    path = fields.Url(required=True, relative=True)

    # pylint: disable=no-self-use, unused-argument
    @validates_schema
    def validate_course_id(self, data, **kwargs):
        """the course_id should be equal to
        "course-v1:{org_id}+{any_string}+{any_string}"
        """
        if data["org_id"] == "" and data["course_id"] != "":
            raise ValidationError("course_id should be empty if org_id is empty")
        if data["course_id"] == "" and data["org_id"] != "":
            raise ValidationError("org_id should be empty if course_id is empty")
        if data["org_id"] == "":
            return
        if not data["course_id"].startswith("course-v1:"):
            raise ValidationError("course_id should starts with 'course-v1'")
        try:
            organization, course, session = (
                data["course_id"].replace("course-v1:", "").split("+")
            )
        except ValueError:
            raise ValidationError(
                "course_id should contain an organization ID, "
                "a course name and session separated by a +"
            )
        if organization != data["org_id"]:
            raise ValidationError(
                "organization ID in the course ID does not match the event organization ID"
            )
        if len(course) == 0 or len(session) == 0:
            raise ValidationError("course and session should not be empty")


class ContextModuleSchema(Schema):
    """Represents the context module field"""

    usage_key = fields.Str(required=True)
    display_name = fields.Str(required=True)


class ContextSchema(BaseContextSchema):
    """Context with module field. Present in Capa problems related
    events.
    """

    module = fields.Nested(ContextModuleSchema(), required=True)

    # pylint: disable=no-self-use
    @validates_schema
    def validate_path(self, data, **kwargs):
        """path should be equal to
        " /courses/{course_id}/xblock/block-v1:{course_id[10:]}"
        "+type@problem+block@{usage_key[-32:]}"
        "/handler/xmodule_handler/problem_check"
        """
        path = data["path"]
        valid_path = (
            f"/courses/"
            f"{data['course_id']}"
            f"/xblock/"
            f"{data['module']['usage_key']}/"
            f"handler/xmodule_handler/problem_check"
        )
        if path != valid_path:
            raise ValidationError(
                f"path should be equal to"
                f"{valid_path}"
                f" and {path} does not match!"
            )


class IPv4AddressField(fields.Field):
    """IPv4 Address that serializes to a string of numbers and deserializes
    to a IPv4Address object.
    """

    def _serialize(self, value, attr, obj, **kwargs):
        if value == "":
            return ""
        return value.exploded

    def _deserialize(self, value, attr, data, **kwargs):
        if value == "":
            return ""
        chunk_ipv4 = r"([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])"
        patten_ipv4 = re.compile(r"^(" + chunk_ipv4 + r"\.){3}" + chunk_ipv4 + r"$")
        # 001.001.001.001 is not a valid ip address
        # IPv4Address("001.001.001.001") => "1.1.1.1"
        # (no exception thrown)
        if not patten_ipv4.match(value):
            raise ValidationError("ip must be empty or a valid IPv4 address")
        try:
            return IPv4Address(value)
        except ValueError as error:
            raise ValidationError("Invalid IPv4 Address") from error


class BaseEventSchema(Schema):
    """Represents the Base Event Schema all events inherit from.
    Does not define event and event_type fields
    """

    # pylint: disable=no-self-argument, no-self-use
    def validate_username(value):
        """"check username field empty or 2-30 chars long"""
        if len(value) == 1 or len(value) > 30:
            raise ValidationError(
                "username should be empty or between 2 and 30 chars long"
            )

    # pylint: disable=no-self-argument, no-self-use
    def validate_referer(value):
        """allow referer be empty"""
        if value != "":
            URL(relative=True)(value)

    username = fields.Str(required=True, validate=validate_username)
    ip = IPv4AddressField(required=True)
    agent = fields.Str(required=True)
    host = fields.Str(required=True)
    referer = fields.Str(required=True, validate=validate_referer)
    accept_language = fields.Str(required=True)
    event_source = fields.Str(
        required=True,
        validate=Equal(
            comparable="server", error='The event event_source field is not "server"'
        ),
    )
    context = fields.Nested(BaseContextSchema(), required=True)
    time = fields.DateTime(format="iso", required=True)
    page = fields.Str(
        required=True,
        allow_none=True,
        validate=Equal(comparable=None, error="The event page field is not None"),
    )
