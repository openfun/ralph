"""Base event model definitions"""

import re
from datetime import datetime
from ipaddress import IPv4Address
from pathlib import Path
from typing import Literal, Optional, Union

from pydantic import AnyUrl, BaseModel, constr, root_validator


class BaseModelWithConfig(BaseModel):
    """Base model defining configuration shared among all models"""

    class Config:  # pylint: disable=missing-class-docstring
        extra = "forbid"


class BaseContextModel(BaseModelWithConfig):
    """Represents the base context model inherited by all event contexts.

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

    course_user_tags: Optional[dict[str, str]]
    user_id: Union[int, Literal[""], None]
    org_id: str
    course_id: str
    path: Path

    @root_validator
    def validate_course_id(
        cls, values
    ):  # pylint: disable=no-self-argument, no-self-use
        """The course_id must match for example `course-v1:org+course+any` or an empty string."""

        org_id = values.get("org_id")
        course_id = values.get("course_id")
        regex = f"course-v1:{org_id}\\+.+\\+.+"
        if (org_id or course_id) and not re.match(regex, course_id):
            raise ValueError(f"course_id must match regex `{regex}`")
        return values


class BaseEventModel(BaseModelWithConfig):
    """Represents the base event model all events inherit from.

    WARNING: it does not define the event and event_type fields.

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
        event_source (str): Consists of the value `server`.
            Note:
                Specifies the source of the interaction that triggered the event.
        context (BaseContextModel): see BaseContextModel.
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
    referer: Union[AnyUrl, Literal[""]]
    accept_language: str
    event_source: Literal["server"]
    context: BaseContextModel
    time: datetime
    page: Union[Literal[None], None]
