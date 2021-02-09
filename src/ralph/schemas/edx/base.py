"""Base event schema definitions"""
from ipaddress import IPv4Address

from marshmallow import Schema, ValidationError, validates, validates_schema
from marshmallow.fields import DateTime, Dict, Field, Nested, Str, Url
from marshmallow.validate import URL, Equal

# pylint: disable=no-self-use, unused-argument


class BaseContextSchema(Schema):
    """Represents the Base Context inherited by all event contexts."""

    course_user_tags = Dict(keys=Str(), values=Str())
    """Consists of a dictionary with key value pairs from the `user_api_usercoursetag` table.

    Retrieved with:
        `dict(
            UserCourseTag.objects.filter(
                user=request.user.pk, course_id=course_key
            ).values_list('key', 'value')
        )`
    Note:
        Is only present when a course page is requested.
        Is an empty dictionary when the user is not logged in or not found in the
        `user_api_usercoursetag` table.
    Source:
        /openedx/core/djangoapps/user_api/middleware.py#L38-L46
    """

    user_id = Field(required=True, allow_none=True)
    """Consists of the ID of the authenticated user.

    Retrieved with:
        `request.user.pk` querying the `auth_user` table.
    Note:
        Is an integer when the user is found in the `auth_user` table.
        Is an empty string when an exception is raised while retrieving the id.
        Is `None` when the user is not logged in.
    Source:
        /common/djangoapps/track/middleware.py#L189
    """

    org_id = Str(required=True)
    """Consists of the organization name that lists the course.

    Retrieved with:
        `course_id.org` where `course_id` is an `opaque_keys.edx.locator.CourseLocator`
        which is created using the URL of the requested page.
    Note:
        Is an empty string when the requested page is not a course page.
    Source:
        /common/djangoapps/track/contexts.py#L55
    """

    course_id = Str(required=True)
    """Consists of the unique identifier for the visited course page.

    Retrieved with:
        `course_id.to_deprecated_string()` where `course_id` is an
        `opaque_keys.edx.locator.CourseLocator` which is created using the URL
        of the requested page.
    Note:
        Is an empty string when the requested page is not a course page.
    Source:
        /common/djangoapps/track/contexts.py#L54
    """

    path = Url(required=True, relative=True)
    """Consist of the relative URL (without the hostname) of the requested page.

    Retrieved with:
        `request.META['PATH_INFO']`
    Source:
        /common/djangoapps/track/middleware.py#L143
    """

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

    Does not define event and event_type fields.
    """

    username = Str(required=True)
    """Consists of the unique username identifying the logged in user.

    Retrieved with:
        `request.user.username` querying the `auth_user` table.
    Note:
        Is an empty string when the user is not logged in.
        If an exception is raised when retrieving the username from the table then
        the value is `anonymous`.
        Usernames are made of 2-30 ASCII letters / numbers / underscores (_) / hyphens (-)
    Source:
        /common/djangoapps/track/views/__init__.py#L95
    """

    ip = Field(required=True)
    """Consists of the public IPv4 address of the user.

    Retrieved with:
        `get_ip(request)` cf. https://github.com/un33k/django-ipware/tree/1.1.0
    Note:
        Can be an empty string if the IP address is not found.
    Source:
        /common/djangoapps/track/views/__init__.py#L102
    """

    agent = Str(required=True)
    """Consists of the `User-Agent` HTTP request header.

    Retrieved with:
        `request.META[HTTP_USER_AGENT]`
    Note:
        Can be an empty string if the header is not present in the request.
        Contains information about:
            Browser name and version
            Operating system name and version
            Default language
    Source:
        /common/djangoapps/track/views/__init__.py#L108
    """

    host = Str(required=True)
    """Consists of the hostname of the server.

    Retrieved with:
        `request.META[SERVER_NAME]`
    Source:
        /common/djangoapps/track/views/__init__.py#L111
    """

    referer = Str(required=True)
    """Consists of the `Referer` HTTP request header.

    Retrieved with:
        `request.META[HTTP_REFERER]`
    Note:
        Can be an empty string if the header is not present in the request.
        Contains the referring url (previous url visited by the user).
    Source:
        /common/djangoapps/track/views/__init__.py#L103
    """

    accept_language = Str(required=True)
    """Consists of the `Accept-Language` HTTP request header.

    Retrieved with:
        `request.META[HTTP_ACCEPT_LANGUAGE]`
    Note:
        Can be an empty string if the header is not present in the request.
        Contains the default language settings of the user.
    Source:
        /common/djangoapps/track/views/__init__.py#L104
    """

    event_source = Str(
        required=True,
        validate=Equal(
            comparable="server", error="The event event_source field is not `server`"
        ),
    )
    """Consists of the value `server`.

    Note:
        Specifies the source of the interaction that triggered the event.
    Source:
        /common/djangoapps/track/views/__init__.py#L105
    """

    context = Nested(BaseContextSchema(), required=True)
    """Consists of a dictionary holding additional information about the request and user.

    Source:
        /common/djangoapps/track/middleware.py#L136
    """

    time = DateTime(format="iso", required=True)
    """Consists of the UTC time in ISO format at which the event was emitted.

    Retrieved with:
        `datetime.datetime.utcnow()`
    Source:
        /common/djangoapps/track/views/__init__.py#L110
    """

    page = Str(
        required=True,
        allow_none=True,
        validate=Equal(comparable=None, error="The event page field is not None"),
    )
    """Consists of the value `None`.

    Note:
        In JSON the value is `null` instead of `None`.
    Source:
        /common/djangoapps/track/views/__init__.py#L109
    """

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
