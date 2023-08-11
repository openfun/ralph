"""Browser event model definitions."""

from typing import Union

try:
    from typing import Annotated, Literal
except ImportError:
    from typing_extensions import Annotated, Literal

from pydantic import StringConstraints, AnyUrl

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
    session: Union[Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{32}$")], Literal[""]]  # noqa: F722
