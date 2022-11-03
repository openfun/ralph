"""Browser event model definitions."""

from typing import Literal, Union

from pydantic import AnyUrl, constr

from .base import BaseEdxModel


class BaseBrowserModel(BaseEdxModel):
    """Pydantic model for core browser statements.

    This type of event is triggered on (XHR) POST/GET requests to the `/event` URL.

    Attributes:
        event_source (str): Consists of the value `browser`.
        page (AnyUrl): Consists of the URL (with hostname) of the visited page.
            Retrieved with:
                `window.location.href` from the JavaScript front-end.
        session (str): Consists of the md5 encrypted Django session key or an empty
            string.
    """

    event_source: Literal["browser"]
    page: AnyUrl
    session: Union[constr(regex=r"^[a-f0-9]{32}$"), Literal[""]]  # noqa: F722
