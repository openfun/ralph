"""Navigational event factory definitions"""

from factory import SubFactory

from ralph.models.edx.navigational import (
    NavigationalEventField,
    PageClose,
    SeqGoto,
    SeqNext,
    SeqPrev,
)

from .base import FAKE, BaseEventFieldFactory
from .browser import BaseBrowserEventFactory


class PageCloseBrowserEventFactory(BaseBrowserEventFactory):
    """Factory for the PageCloseBrowserEventModel."""

    class Meta:  # pylint: disable=missing-class-docstring
        model = PageClose

    name = "page_close"
    event_type = "page_close"
    event = "{}"


class SeqGotoBrowserEventEventFieldFactory(BaseEventFieldFactory):
    """Factory for the SeqGotoBrowserEventEventFieldModel."""

    class Meta:  # pylint: disable=missing-class-docstring
        model = NavigationalEventField

    id = (
        "block-v1:universityX+CS111+2020_T1"
        "+type@sequential+block@d0d4a647742943e3951b45d9db8a0ea1"
    )
    old = FAKE.pyint()
    new = FAKE.pyint()


class SeqGotoBrowserEventFactory(BaseBrowserEventFactory):
    """Factory for the SeqGotoBrowserEventModel."""

    class Meta:  # pylint: disable=missing-class-docstring
        model = SeqGoto

    name = "seq_goto"
    event_type = "seq_goto"
    event = SubFactory(SeqGotoBrowserEventEventFieldFactory)


class SeqNextBrowserEventEventFieldFactory(BaseEventFieldFactory):
    """Factory for the SeqGotoBrowserEventEventFieldModel."""

    class Meta:  # pylint: disable=missing-class-docstring
        model = NavigationalEventField

    id = (
        "block-v1:universityX+CS111+2020_T1"
        "+type@sequential+block@d0d4a647742943e3951b45d9db8a0ea1"
    )
    old = FAKE.pyint()
    new = old + 1


class SeqNextBrowserEventFactory(BaseBrowserEventFactory):
    """Factory for the SeqNextBrowserEventModel."""

    class Meta:  # pylint: disable=missing-class-docstring
        model = SeqNext

    name = "seq_next"
    event_type = "seq_next"
    event = SubFactory(SeqNextBrowserEventEventFieldFactory)


class SeqPrevBrowserEventEventFieldFactory(BaseEventFieldFactory):
    """Factory for the SeqPrevBrowserEventEventFieldModel."""

    class Meta:  # pylint: disable=missing-class-docstring
        model = NavigationalEventField

    id = (
        "block-v1:universityX+CS111+2020_T1"
        "+type@sequential+block@d0d4a647742943e3951b45d9db8a0ea1"
    )
    old = FAKE.pyint()
    new = old - 1


class SeqPrevBrowserEventFactory(BaseBrowserEventFactory):
    """Factory for the SeqPrevBrowserEventModel."""

    class Meta:  # pylint: disable=missing-class-docstring
        model = SeqPrev

    name = "seq_prev"
    event_type = "seq_prev"
    event = SubFactory(SeqPrevBrowserEventEventFieldFactory)
