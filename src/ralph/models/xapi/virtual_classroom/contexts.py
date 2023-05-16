"""Virtual classroom xAPI events context fields definitions."""

from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

try:
    from typing import Literal  # pylint: disable = ungrouped-imports
except ImportError:
    from typing_extensions import Literal

from pydantic import Field

from ..base.contexts import BaseXapiContext, BaseXapiContextContextActivities
from ..base.unnested_objects import BaseXapiActivity
from ..concepts.activity_types.scorm_profile import ProfileActivity
from ..concepts.activity_types.virtual_classroom import VirtualClassroomActivity
from ..concepts.constants.cmi5_profile import CONTEXT_EXTENSION_SESSION_ID
from ..concepts.constants.tincan_vocabulary import CONTEXT_EXTENSION_PLANNED_DURATION
from ..config import BaseExtensionModelWithConfig


class VirtualClassroomContextActivitiesCategory(BaseXapiActivity):
    # noqa: D205, D415
    """Pydantic model for virtual classroom `context`.`contextActivities`.`category`
    property.

    Attributes:
        id (str): Consists of the value `https://w3id.org/xapi/virtual-classroom`.
        definition (dict): see ProfileActivity.
    """

    id: Literal[
        "https://w3id.org/xapi/virtual-classroom"
    ] = "https://w3id.org/xapi/virtual-classroom"
    definition: ProfileActivity


class VirtualClassroomContextContextActivities(BaseXapiContextContextActivities):
    """Pydantic model for virtual classroom `context`.`contextActivities` property.

    Attributes:
        category (list): see VirtualClassroomContextActivitiesCategory.
    """

    category: Union[
        VirtualClassroomContextActivitiesCategory,
        List[VirtualClassroomContextActivitiesCategory],
    ]


class VirtualClassroomContextExtensions(BaseExtensionModelWithConfig):
    """Pydantic model for virtual classroom base `context`.`extensions` property.

    Attributes:
        session_id (str): Consists of the ID of the active session.
    """

    session_id: str = Field(alias=CONTEXT_EXTENSION_SESSION_ID, default="")


class VirtualClassroomContext(BaseXapiContext):
    """Pydantic model for virtual classroom base `context` property.

    Attributes:
        registration (uuid): the registration that the Statement is associated with.
        extensions (dict): see VirtualClassroomExtensions.
    """

    contextActivities: VirtualClassroomContextContextActivities
    registration: UUID
    extensions: VirtualClassroomContextExtensions


# Initialized statement


class VirtualClassroomInitializedContextExtensions(VirtualClassroomContextExtensions):
    """Pydantic model for virtual classroom initialized `context`.`extensions` property.

    Attributes:
        planned_duration (datetime): Consists of the estimated duration of the scheduled
            virtual classroom.
    """

    planned_duration: Optional[datetime] = Field(
        alias=CONTEXT_EXTENSION_PLANNED_DURATION
    )


class VirtualClassroomInitializedContext(VirtualClassroomContext):
    """Pydantic model for virtual classroom initialized `context` property.

    Attributes:
        extensions (dict): see VirtualClassroomInitializedContextExtensions.
    """

    extensions: VirtualClassroomInitializedContextExtensions


# Joined statement


class VirtualClassroomJoinedContextExtensions(VirtualClassroomContextExtensions):
    """Pydantic model for virtual classroom initialized `context`.`extensions` property.

    Attributes:
        planned_duration (datetime): Consists of the estimated duration of the scheduled
            virtual classroom.
    """

    planned_duration: Optional[datetime] = Field(
        alias=CONTEXT_EXTENSION_PLANNED_DURATION
    )


class VirtualClassroomJoinedContext(VirtualClassroomContext):
    """Pydantic model for virtual classroom joined `context` property.

    Attributes:
        extensions (dict): see VirtualClassroomJoinedContextExtensions.
    """

    extensions: VirtualClassroomJoinedContextExtensions


# Terminated statement


class VirtualClassroomTerminatedContextExtensions(VirtualClassroomContextExtensions):
    """Pydantic model for virtual classroom terminated `context`.`extensions` property.

    Attributes:
        planned_duration (datetime): Consists of the estimated duration of the scheduled
            virtual classroom.
    """

    planned_duration: Optional[datetime] = Field(
        alias=CONTEXT_EXTENSION_PLANNED_DURATION
    )


class VirtualClassroomTerminatedContext(VirtualClassroomContext):
    """Pydantic model for virtual classroom terminated `context` property.

    Attributes:
        extensions (dict): see VirtualClassroomInitializedContextExtensions.
    """

    extensions: VirtualClassroomTerminatedContextExtensions


class VirtualClassroomStartedPollContextActivities(
    VirtualClassroomContextContextActivities
):
    # noqa: D205, D415
    """Pydantic model for virtual classroom started poll `context`.`contextActivities`
    property.

    Attributes:
        parent (list): see VirtualClassroomActivity.
    """

    parent: Union[VirtualClassroomActivity, List[VirtualClassroomActivity]]


class VirtualClassroomStartedPollContext(VirtualClassroomContext):
    """Pydantic model for virtual classroom started poll `context` property.

    Attributes:
        extensions (dict): see VirtualClassroomContextExtensions.
        contextActivities (dict): see
            VirtualClassroomStartedPollContextActivities.
    """

    extensions: VirtualClassroomContextExtensions
    contextActivities: VirtualClassroomStartedPollContextActivities


# Answered poll statement


class VirtualClassroomAnsweredPollContextActivities(
    VirtualClassroomContextContextActivities
):
    # noqa: D205, D415
    """Pydantic model for virtual classroom answered poll `context`.`contextActivities`
    property.

    Attributes:
        parent (list): see VirtualClassroomActivity.
    """

    parent: Union[VirtualClassroomActivity, List[VirtualClassroomActivity]]


class VirtualClassroomAnsweredPollContext(VirtualClassroomContext):
    """Pydantic model for virtual classroom answered poll `context` property.

    Attributes:
        extensions (dict): see VirtualClassroomContextExtensions.
        contextActivities (dict): see VirtualClassroomAnsweredPollContextActivities.
    """

    extensions: VirtualClassroomContextExtensions
    contextActivities: VirtualClassroomAnsweredPollContextActivities


# Posted public message statement


class VirtualClassroomPostedPublicMessageContextActivities(
    VirtualClassroomContextContextActivities
):
    # noqa: D205, D415
    """Pydantic model for virtual classroom posted public message
    `context`.`contextActivities` property.

    Attributes:
        parent (list): see VirtualClassroomActivity.
    """

    parent: Union[VirtualClassroomActivity, List[VirtualClassroomActivity]]


class VirtualClassroomPostedPublicMessageContext(VirtualClassroomContext):
    """Pydantic model for virtual classroom posted public message `context` property.

    Attributes:
        extensions (dict): see VirtualClassroomContextExtensions.
        contextActivities (list): see
            VirtualClassroomPostedPublicMessageContextActivities.
    """

    extensions: VirtualClassroomContextExtensions
    contextActivities: VirtualClassroomPostedPublicMessageContextActivities
