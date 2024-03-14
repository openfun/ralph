"""Course Content Completion event fields definitions."""

from ...base import AbstractBaseEventField


class EdxDoneToggledEventField(AbstractBaseEventField):
    """Pydantic model for course content completion core `event` field.

    Attributes:
        done (bool): Consists of the state of the Completion toggle when event
        is emitted. Set to `true` when the learner has completed the associated
        content and `false` otherwise.
    """

    done: bool
