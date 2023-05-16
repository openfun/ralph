"""Virtual classroom xAPI events result fields definitions."""

from pydantic import StrictStr

from ..base.results import BaseXapiResult


class VirtualClassroomAnsweredPollResult(BaseXapiResult):
    """Pydantic model for virtual classroom answered poll `result` property.

    Attributes:
        response (str): Consists of the response for the given Activity.
    """

    response: StrictStr  # = StrictStr()
