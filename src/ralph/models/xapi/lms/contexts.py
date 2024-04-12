"""LMS xAPI events context fields definitions."""

import sys
from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from pydantic import Field, NonNegativeFloat, PositiveInt, condecimal, field_validator
from typing_extensions import Annotated

from ..base.contexts import BaseXapiContext, BaseXapiContextContextActivities
from ..base.unnested_objects import BaseXapiActivity
from ..concepts.activity_types.scorm_profile import ProfileActivity
from ..concepts.constants.cmi5_profile import CONTEXT_EXTENSION_SESSION_ID
from ..concepts.constants.lms import (
    CONTEXT_EXTENSION_ENDING_DATE,
    CONTEXT_EXTENSION_ROLE,
    CONTEXT_EXTENSION_STARTING_DATE,
)
from ..concepts.constants.video import (
    CONTEXT_EXTENSION_LENGTH,
    CONTEXT_EXTENSION_QUALITY,
)
from ..config import BaseExtensionModelWithConfig

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class LMSProfileActivity(ProfileActivity):
    """Pydantic model for LMS `profile` activity type.

    Attributes:
        id (str): Consists of the value `https://w3id.org/xapi/lms`.
    """

    id: Literal["https://w3id.org/xapi/lms"] = "https://w3id.org/xapi/lms"


class LMSContextContextActivities(BaseXapiContextContextActivities):
    """Pydantic model for LMS `context`.`contextActivities` property.

    Attributes:
        category (dict or list): see LMSProfileActivity.
    """

    category: Union[
        LMSProfileActivity, List[Union[LMSProfileActivity, BaseXapiActivity]]
    ]

    @field_validator("category")
    @classmethod
    def check_presence_of_profile_activity_category(
        cls,
        value: Union[
            LMSProfileActivity, List[Union[LMSProfileActivity, BaseXapiActivity]]
        ],
    ) -> Union[LMSProfileActivity, List[Union[LMSProfileActivity, BaseXapiActivity]]]:
        """Check that the category list contains a `LMSProfileActivity`."""
        if isinstance(value, LMSProfileActivity):
            return value
        for activity in value:
            if isinstance(activity, LMSProfileActivity):
                return value
        raise ValueError(
            "The `context.contextActivities.category` field should contain at least "
            "one valid `LMSProfileActivity`"
        )


class LMSContext(BaseXapiContext):
    """Pydantic model for LMS base `context` property.

    Attributes:
        contextActivities (dict): see LMSContextContextActivities.
    """

    contextActivities: LMSContextContextActivities


# Registered to a course/Unregistered to a course


class LMSRegistrationContextExtensions(BaseExtensionModelWithConfig):
    """Pydantic model for LMS registration `context`.`extensions` property.

    Attributes:
        starting_date (datetime): Starting date of the activity, formatted according to
            the normal format of ISO 8601.
        ending_date (datetime): Ending date of the activity, formatted according to the
            normal format of ISO 8601.
        role (str): Role of the actor. For example: `admin`, `manager`, `teacher`,
            `guest`, `learner` or `staff`.
    """

    starting_date: Annotated[
        Optional[datetime], Field(alias=CONTEXT_EXTENSION_STARTING_DATE)
    ] = None
    ending_date: Annotated[
        Optional[datetime], Field(alias=CONTEXT_EXTENSION_ENDING_DATE)
    ] = None
    role: Annotated[Optional[str], Field(alias=CONTEXT_EXTENSION_ROLE)]


class LMSRegistrationContext(LMSContext):
    """Pydantic model for LMS registration statements `context` property.

    This model is used for `registered to a course` and
    `unregistered to a course` statement templates.

    Attributes:
        extensions (dict): see LMSRegistrationContextExtensions.
    """

    extensions: Optional[LMSRegistrationContextExtensions] = None


class LMSCommonContextExtensions(BaseExtensionModelWithConfig):
    """Pydantic model for common LMS statements `context`.`extensions` property.

    This model is used for `downloaded a video`, `downloaded a document`,
    `downloaded an audio`, `downloaded a file`,  `uploaded a video`,
    `uploaded a document` and `uploaded an audio`, `uploaded a file`
    statement templates.

    Attributes:
        session_id (uuid): ID of the active session.
    """

    session_id: Annotated[Optional[UUID], Field(alias=CONTEXT_EXTENSION_SESSION_ID)] = (
        None
    )


class LMSCommonContext(LMSContext):
    """Pydantic model for LMS common `context` property.

    Attributes:
        extensions (dict): See LMSCommonContextExtensions.
    """

    extensions: Optional[LMSCommonContextExtensions] = None


class LMSDownloadedVideoContextExtensions(LMSCommonContextExtensions):
    """Pydantic model for LMS downloaded video `context`.`extensions` property.

    Attributes:
        length (float): Length of the video.
        quality (int): Video resolution or quality of the video.
    """

    length: Annotated[
        Optional[condecimal(ge=0, decimal_places=3)],
        Field(alias=CONTEXT_EXTENSION_LENGTH),
    ] = None
    quality: Annotated[
        Optional[PositiveInt], Field(alias=CONTEXT_EXTENSION_QUALITY)
    ] = None


class LMSDownloadedVideoContext(LMSContext):
    """Pydantic model for LMS downloaded video `context` property.

    Attributes:
        extensions (dict): See LMSDownloadedVideoContextExtensions.
    """

    extensions: Optional[LMSDownloadedVideoContextExtensions] = None


class LMSDownloadedAudioContextExtensions(LMSCommonContextExtensions):
    """Pydantic model for LMS downloaded audio `context`.`extensions` property.

    Attributes:
        length (float): Length of the audio.
    """

    length: Annotated[
        Optional[NonNegativeFloat], Field(alias=CONTEXT_EXTENSION_LENGTH)
    ] = None


class LMSDownloadedAudioContext(LMSContext):
    """Pydantic model for LMS downloaded audio `context` property.

    Attributes:
        extensions (dict): See LMSDownloadedAudioContextExtensions.
    """

    extensions: Optional[LMSDownloadedAudioContextExtensions] = None
