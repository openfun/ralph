"""Virtual classroom xAPI events result fields definitions."""

from ..base.results import BaseXapiResult

from ralph.conf import NonEmptyStrictStr

class VirtualClassroomAnsweredPollResult(BaseXapiResult):
    """Pydantic model for virtual classroom answered poll `result` property.

    Attributes:
        response (str): Consists of the response for the given Activity.
    """

    response: NonEmptyStrictStr  # = StrictStr()
