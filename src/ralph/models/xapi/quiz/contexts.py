"""`Assessment` xAPI events context fields definitions."""

from typing import List, Union

from ..base.contexts import BaseXapiContext, BaseXapiContextContextActivities
from ..base.unnested_objects import BaseXapiActivity, BaseXapiActivityDefinition
from ..concepts.constants.quiz import PROFILE_ID_QUIZ
from ..concepts.constants.scorm_profile import ACTIVITY_ID_PROFILE


class QuizContextActivitiesCategoryDefinition(BaseXapiActivityDefinition):
    # noqa: D205
    """Pydantic model for quiz `context`.`contextActivities`.`category`.
    `definition` property.

    Attributes:
        type (str): Consists of the value `http://adlnet.gov/expapi/activities/profile`.
    """

    type: ACTIVITY_ID_PROFILE = ACTIVITY_ID_PROFILE.__args__[0]


class QuizContextActivitiesCategory(BaseXapiActivity):
    # noqa: D205, D415
    """Pydantic model for quiz `context`.`contextActivities`.`category`
    property.

    Attributes:
        id (str): Consists of the value `https://w3id.org/xapi/quiz`.
        definition (dict): see QuizContextActivitiesCategoryDefinition.
    """

    id: PROFILE_ID_QUIZ = PROFILE_ID_QUIZ.__args__[0]
    definition: QuizContextActivitiesCategoryDefinition = (
        QuizContextActivitiesCategoryDefinition()
    )


class QuizContextActivities(BaseXapiContextContextActivities):
    """Pydantic model for quiz `context`.`contextActivities` property.

    Attributes:
        category (list): see QuizContextActivitiesCategory.
    """

    category: Union[
        QuizContextActivitiesCategory,
        List[QuizContextActivitiesCategory],
    ]


class QuizContext(BaseXapiContext):
    """Pydantic model for quiz base `context` property.

    Attributes:
        contextActivities: see QuizContextActivities.
    """

    contextActivities: QuizContextActivities
