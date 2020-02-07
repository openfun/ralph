"""
Ralph tracking logs filters.
"""
from .exceptions import EventKeyError


def anonymous(events):
    """Remove anonymous events.

    Args:
        events (DataFrame): events to filter

    Returns:
        Filtered pandas DataFrame.

    """

    if events.get("username", None) is None:
        raise EventKeyError(
            "Cannot filter anonymous filters without 'username' column."
        )
    return events.loc[lambda df: df["username"] != "", :]
