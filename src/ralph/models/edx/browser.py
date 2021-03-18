"""Browser event model definitions"""

from pathlib import Path
from typing import Literal, Union

from pydantic import AnyUrl, constr

from ralph.models.selector import selector

from .base import BaseEventModel


class BaseBrowserEventModel(BaseEventModel):
    """Represents the base browser event model all browser events inherit from.

    This type of event is triggered on (XHR) POST/GET requests to the `/event` URL.

    Attributes:
        event_source (str): Consists of the value `browser`.
        page (Path): Consists of the URL (with hostname) of the visited page.
            Retrieved with:
                `window.location.href` from the JavaScript front-end.
        session (str): Consists of the md5 encrypted Django session key or an empty string
    """

    event_source: Literal["browser"]
    page: Union[AnyUrl, Path]
    session: Union[constr(regex=r"^[a-f0-9]{32}$"), Literal[""]]  # noqa: F722


class PageCloseBrowserEventModel(BaseBrowserEventModel):
    """Represents the page_close browser event.

    This type of event is triggered when the user navigates to the next page
    or closes the browser window (when the JavaScript `window.onunload` event
    is called).

    Attributes:
        name (str): Consists of the value `page_close`
        event_type (str): Consists of the value `page_close`
        event (str): Consists of the string value `{}`
    """

    __selector__ = selector(event_source="browser", event_type="page_close")

    # pylint: disable=unsubscriptable-object
    name: Literal["page_close"]
    event_type: Literal["page_close"]
    event: Literal["{}"]
