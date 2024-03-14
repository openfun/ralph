"""Survey event model definitions."""

import sys
from typing import Union

from pydantic import Json

from ralph.models.edx.survey.fields.events import XBlockSurveySubmittedEventField
from ralph.models.selector import selector

from ..server import BaseServerModel

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class XBlockSurveySubmitted(BaseServerModel):
    """Pydantic model for `xblock.survey.submitted` statement.

    The server emits this statement when a user submits a response to a survey.

    Attributes:
        event (XBlockSurveySubmittedEventField): See XBlockSurveySubmittedEventField.
        event_type (str): Consists of the value `xblock.survey.submitted`.
        name (str): Consists either of the value `xblock.survey.submitted`.
    """

    __selector__ = selector(event_source="server", event_type="xblock.survey.submitted")

    event: Union[
        Json[XBlockSurveySubmittedEventField],
        XBlockSurveySubmittedEventField,
    ]
    event_type: Literal["xblock.survey.submitted"]
    name: Literal["xblock.survey.submitted"]


class XBlockSurveyViewResults(BaseServerModel):
    """Pydantic model for `xblock.survey.view_results` statement.

    The server emits this statement when a tally of poll answers is displayed to a user.

    Attributes:
        event_type (str): Consists of the value `xblock.survey.view_results`.
        name (str): Consists either of the value `xblock.survey.view_results`.
    """

    __selector__ = selector(
        event_source="server", event_type="xblock.survey.view_results"
    )

    event_type: Literal["xblock.survey.view_results"]
    name: Literal["xblock.survey.view_results"]
