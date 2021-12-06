"""Open Response Assessment events model definitions"""

from typing import Literal

from ralph.models.edx.server import BaseServerModel
from ralph.models.selector import selector

from .fields.events import ORASaveSubmissionEventField


class ORASaveSubmission(BaseServerModel):
    """Represents the `openassessmentblock.save_submission` event.

    This event is triggered when the user clicks on the <kbd>Save your progress</kbd>
    button to save the current state of his response to an open assessment question.

    Attributes:
        event (str): See ORASaveSubmissionEventField.
        event_type (str): Consists of the value `openassessmentblock.save_submission`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(
        event_source="server", event_type="openassessmentblock.save_submission"
    )

    event: ORASaveSubmissionEventField
    event_type: Literal["openassessmentblock.save_submission"]
    page: Literal["x_module"]
