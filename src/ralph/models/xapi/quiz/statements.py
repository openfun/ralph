"""`Quiz` xAPI event definitions."""

from datetime import datetime

from ...selector import selector
from ..base.statements import BaseXapiStatement
from ..concepts.activity_types.scorm_profile import CMIInteractionActivity
from ..concepts.verbs.adl_vocabulary import LaunchedVerb
from ..concepts.verbs.scorm_profile import (
    CompletedVerb,
    FailedVerb,
    InitializedVerb,
    PassedVerb,
    TerminatedVerb,
)
from .contexts import QuizContext

# Mandatory statements


class QuizInitialized(BaseXapiStatement):
    """Pydantic model for quiz initialized statement.

    Example:

    Attributes:
        verb (dict): See InitializedVerb.
        object (dict): See CMIInteractionActivity.
        context (dict): See QuizContext.
        timestamp (datetime): Consists of the timestamp of when the event occurred.
    """

    __selector__ = selector(
        verb__id="http://adlnet.gov/expapi/verbs/initialized",
        object__definition__type=(
            "http://adlnet.gov/expapi/activities/cmi.interaction"
        ),
    )

    verb: InitializedVerb = InitializedVerb()
    object: CMIInteractionActivity
    context: QuizContext
    timestamp: datetime


class QuizLaunched(BaseXapiStatement):
    """Pydantic model for quiz launched statement.

    Example:

    Attributes:
        verb (dict): See LaunchedVerb.
        object (dict): See CMIInteractionActivity.
        context (dict): See QuizContext.
        timestamp (datetime): Consists of the timestamp of when the event occurred.
    """

    __selector__ = selector(
        verb__id="http://adlnet.gov/expapi/verbs/launched",
        object__definition__type=(
            "http://adlnet.gov/expapi/activities/cmi.interaction"
        ),
    )

    verb: LaunchedVerb = LaunchedVerb()
    object: CMIInteractionActivity
    context: QuizContext
    timestamp: datetime


class QuizPassed(BaseXapiStatement):
    """Pydantic model for quiz passed statement.

    Example:

    Attributes:
        verb (dict): See PassedVerb.
        object (dict): See CMIInteractionActivity.
        context (dict): See QuizContext.
        timestamp (datetime): Consists of the timestamp of when the event occurred.
    """

    __selector__ = selector(
        verb__id="http://adlnet.gov/expapi/verbs/passed",
        object__definition__type=(
            "http://adlnet.gov/expapi/activities/cmi.interaction"
        ),
    )

    verb: PassedVerb = PassedVerb()
    object: CMIInteractionActivity
    context: QuizContext
    timestamp: datetime


class QuizFailed(BaseXapiStatement):
    """Pydantic model for quiz failed statement.

    Example:

    Attributes:
        verb (dict): See FailedVerb.
        object (dict): See CMIInteractionActivity.
        context (dict): See QuizContext.
        timestamp (datetime): Consists of the timestamp of when the event occurred.
    """

    __selector__ = selector(
        verb__id="http://adlnet.gov/expapi/verbs/passed",
        object__definition__type=(
            "http://adlnet.gov/expapi/activities/cmi.interaction"
        ),
    )

    verb: FailedVerb = FailedVerb()
    object: CMIInteractionActivity
    context: QuizContext
    timestamp: datetime


class QuizCompleted(BaseXapiStatement):
    """Pydantic model for quiz completed statement.

    Example:

    Attributes:
        verb (dict): See CompletedVerb.
        result (dict): See CMIInteractionActivity.
        context (dict): See .
    """

    __selector__ = selector(
        object__definition__type="http://adlnet.gov/expapi/activities/cmi.interaction",
        verb__id="http://adlnet.gov/expapi/verbs/completed",
    )

    verb: CompletedVerb = CompletedVerb()
    result: CMIInteractionActivity
    context: QuizContext
    timestamp: datetime


class QuizTerminated(BaseXapiStatement):
    """Pydantic model for quiz terminated statement.

    Example:

    Attributes:
        verb (dict): See CompletedVerb.
        result (dict): See CMIInteractionActivity.
        context (dict): See .
    """

    __selector__ = selector(
        object__definition__type="http://adlnet.gov/expapi/activities/cmi.interaction",
        verb__id="http://adlnet.gov/expapi/verbs/terminated",
    )

    verb: TerminatedVerb = TerminatedVerb()
    result: CMIInteractionActivity
    context: QuizContext
    timestamp: datetime
