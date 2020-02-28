"""Ralph xAPI formatter"""

import logging

from ralph.exceptions import NotImplementedStatementType
from .problem import ProblemCheck

logger = logging.getLogger(__name__)


statement_types = {"problem_check": ProblemCheck}


def factory(event):
    """Get xAPI statement instance given an event type

    Args:
        event: a parsed tracking log event.

    Returns:
        Statement: an xAPI statement instance.

    """
    logger.debug("Event type: %s", event.event_type)

    statement_class = statement_types.get(event.event_type)

    if statement_class is None:
        raise NotImplementedStatementType(
            f"Unsupported event type: '{event.event_type}'"
        )

    return statement_class(event)
