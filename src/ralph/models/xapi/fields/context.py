"""Common xAPI context field definitions"""

from ipaddress import IPv4Address
from pathlib import Path
from typing import Optional

from pydantic import Field, constr

from ..config import BaseModelWithConfig
from ..constants import (
    XAPI_EXTENSION_ACCEPT_LANGUAGE,
    XAPI_EXTENSION_AGENT,
    XAPI_EXTENSION_COURSE_ID,
    XAPI_EXTENSION_COURSE_USER_TAGS,
    XAPI_EXTENSION_HOST,
    XAPI_EXTENSION_IP,
    XAPI_EXTENSION_ORG_ID,
    XAPI_EXTENSION_PATH,
    XAPI_EXTENSION_SESSION,
)


class ContextExtensionsField(BaseModelWithConfig):
    """Represents the `context.extensions` xAPI field.

    WARNING: It don't include the optional `referer` field.

    Attributes:
        ip (IPv4Address): Consists of the public IPv4 address of the user. (Optional)
        agent (str): Consists of the `User-Agent` HTTP request header. (Optional)
        host (str): Consists of the hostname of the server. (Optional)
        accept_language (str): Consists of the `Accept-Language` HTTP request header. (Optional)
        course_id (str): Consists of the unique identifier for the visited course page. (Optional)
        course_user_tags (str): Content from `user_api_usercoursetag` table. (Optional)
    """

    ip: Optional[IPv4Address] = Field(alias=XAPI_EXTENSION_IP)
    agent: Optional[str] = Field(alias=XAPI_EXTENSION_AGENT)
    host: Optional[str] = Field(alias=XAPI_EXTENSION_HOST)
    accept_language: Optional[str] = Field(alias=XAPI_EXTENSION_ACCEPT_LANGUAGE)
    course_id: Optional[str] = Field(alias=XAPI_EXTENSION_COURSE_ID)
    course_user_tags: Optional[dict[str, str]] = Field(
        alias=XAPI_EXTENSION_COURSE_USER_TAGS
    )
    org_id: Optional[str] = Field(alias=XAPI_EXTENSION_ORG_ID)
    path: Optional[Path] = Field(alias=XAPI_EXTENSION_PATH)
    session: Optional[constr(regex=r"^[a-f0-9]{32}$")] = Field(  # noqa: F722
        alias=XAPI_EXTENSION_SESSION
    )


class ContextField(BaseModelWithConfig):
    """Represents the `context` xAPI field.

    WARNING: It don't include the optional `registration`, `instructor`, `team`,
    `contextActivities`, `revision`, `platform`, `language` and `statement` fields.

    Attributes:
        extensions (ContextExtensionsField): See ContextExtensionsField.
    """

    extensions: ContextExtensionsField
