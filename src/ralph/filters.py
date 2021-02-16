"""
Ralph tracking logs filters.
"""
from .exceptions import EventKeyError


def anonymous(event):
    """Remove anonymous events.

    Args:
        event (dict): event to filter

    Returns:
        event (dict): when event is not anonymous
        None: otherwise

    Raises:
        EventKeyError: When the event does not contain the `username` key.

    """

    if "username" not in event:
        raise EventKeyError("Cannot filter anonymous event without 'username' key.")
    if not event.get("username", ""):
        return None

    return event
