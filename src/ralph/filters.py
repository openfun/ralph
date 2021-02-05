"""
Ralph tracking logs filters.
"""

from .exceptions import EventKeyError


def anonymous(event):
    """Remove anonymous event.

    Args:
        event (dict): event to filter

    Returns:
        event (dict): when event is not anonymous
        None: otherwise

    """

    username = event.get("username", None)
    if username is None:
        raise EventKeyError("Cannot filter anonymous event without 'username' key.")
    if not username:
        return None
    return event
