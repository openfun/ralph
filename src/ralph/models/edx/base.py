"""Base event model definitions"""

from datetime import datetime
from ipaddress import IPv4Address
from pathlib import Path
from typing import Dict, Literal, Optional, Union

from pydantic import BaseModel, HttpUrl, constr


class BaseModelWithConfig(BaseModel):
    """Base model defining configuration shared among all models."""

    class Config:  # pylint: disable=missing-class-docstring
        extra = "forbid"


class BaseContextField(BaseModelWithConfig):
    """Represents the base context field model inherited by all event `context` fields.

    Attributes:
        course_user_tags (dict of str): Content from `user_api_usercoursetag` table.
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
        user_id (int or str or None): Consists of the ID of the authenticated user.
            Retrieved with:
                `request.user.pk` querying the `auth_user` table.
            Note:
                Is an integer when the user is found in the `auth_user` table.
                Is an empty string when an exception is raised while retrieving the ID.
                Is `None` when the user is not logged in.
        org_id (str): Consists of the organization name that lists the course.
            Retrieved with:
                `course_id.org` where `course_id` is an `opaque_keys.edx.locator.CourseLocator`
                which is created using the URL of the requested page.
            Note:
                Is an empty string when the requested page is not a course page.
        course_id (str): Consists of the unique identifier for the visited course page.
            Retrieved with:
                `course_id.to_deprecated_string()` where `course_id` is an
                `opaque_keys.edx.locator.CourseLocator` which is created using the URL
                of the requested page.
            Note:
                Is an empty string when the requested page is not a course page.
        path (Path): Consist of the relative URL (without the hostname) of the requested page.
            Retrieved with:
                `request.META['PATH_INFO']`
    """

    course_user_tags: Optional[Dict[str, str]]
    user_id: Union[int, Literal[""], None]
    org_id: str
    course_id: constr(regex=r"^$|^course-v1:.+\+.+\+.+$")  # noqa:F722
    path: Path


class AbstractBaseEventField(BaseModelWithConfig):
    """Represents the base event field model inherited by all event `event` fields.

    The base model does not have any attributes as event field does not have common sub-fields.
    """


class BaseEvent(BaseModelWithConfig):
    """Represents the base event model all events inherit from.

    WARNING: it does not define the `event`, `event_type` and `event_source` fields.

    Attributes:
        username (str): Consists of the unique username identifying the logged in user.
            Retrieved with:
                `request.user.username` querying the `auth_user` table.
            Note:
                Is an empty string when the user is not logged in.
                If an exception is raised when retrieving the username from the table then
                the value is `anonymous`.
                Usernames are made of 2-30 ASCII letters / numbers / underscores (_) / hyphens (-)
        ip (IPv4Address or str): Consists of the public IPv4 address of the user.
            Retrieved with:
                `get_ip(request)` cf. https://github.com/un33k/django-ipware/tree/1.1.0
            Note:
                Can be an empty string if the IP address is not found.
        agent (str): Consists of the `User-Agent` HTTP request header.
            Retrieved with:
                `request.META[HTTP_USER_AGENT]`
            Note:
                Can be an empty string if the header is not present in the request.
                Contains information about:
                    Browser name and version
                    Operating system name and version
                    Default language
        host (str): Consists of the hostname of the server.
            Retrieved with:
                `request.META[SERVER_NAME]`
        referer (Path): Consists of the `Referer` HTTP request header.
            Retrieved with:
                `request.META[HTTP_REFERER]`
            Note:
                Can be an empty string if the header is not present in the request.
                Contains the referring URL (previous URL visited by the user).
        accept_language (str): Consists of the `Accept-Language` HTTP request header.
            Retrieved with:
                `request.META[HTTP_ACCEPT_LANGUAGE]`
            Note:
                Can be an empty string if the header is not present in the request.
                Contains the default language settings of the user.
        context (BaseContextField): see BaseContextField.
        time (datetime): Consists of the UTC time in ISO format at which the event was emitted.
            Retrieved with:
                `datetime.datetime.utcnow()`
        page (None): Consists of the value `None`
            Note:
                In JSON the value is `null` instead of `None`.
    """

    username: Union[constr(min_length=2, max_length=30), Literal[""]]
    ip: Union[IPv4Address, Literal[""]]
    agent: str
    host: str
    referer: Union[HttpUrl, Literal[""]]
    accept_language: str
    context: BaseContextField
    time: datetime
    page: Union[Literal[None], None]
