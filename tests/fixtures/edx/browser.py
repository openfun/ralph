"""Browser event factory definitions"""

from ralph.models.edx.browser import BaseBrowserEventModel

from .base import FAKE, BaseEventFactory


class BaseBrowserEventFactory(BaseEventFactory):
    """Base browser event factory inherited by all browser event factories."""

    class Meta:  # pylint: disable=missing-class-docstring
        model = BaseBrowserEventModel

    event_source = "browser"
    page = FAKE.url()
    session = FAKE.md5(raw_output=False)
