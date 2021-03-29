"""Browser event model definitions"""

from pathlib import Path
from typing import Literal, Union

from pydantic import AnyUrl, constr

from .base import BaseEvent


class BaseBrowserEvent(BaseEvent):
    """Represents the base browser event model all browser events inherit from.

    This type of event is triggered on (XHR) POST/GET requests to the `/event` URL.

    Attributes:
        event_source (str): Consists of the value `browser`.
        page (Path): Consists of the URL (with hostname) of the visited page.
            Retrieved with:
                `window.location.href` from the JavaScript front-end.
        session (str): Consists of the md5 encrypted Django session key or an empty string.
    """

    event_source: Literal["browser"]
    page: Union[AnyUrl, Path]
    session: Union[constr(regex=r"^[a-f0-9]{32}$"), Literal[""]]  # noqa: F722
