"""Ralph xAPI formatter utils."""

from ralph.exceptions import EventKeyError
from ralph.settings import LMS_PLATFORM_URI


def activity_identifier(event):
    """Get a unique activity identifier for an event."""

    try:
        key = event.context["module"]["usage_key"]
    except KeyError:
        raise EventKeyError(f"Expected context.module.usage_key in event {event}")

    return f"{LMS_PLATFORM_URI}/xblock/{key}"


def activity_name(event):
    """Get activity display name for an event."""

    try:
        name = event.context["module"]["display_name"]
    except KeyError:
        raise EventKeyError(f"Expected context.module.display_name in event {event}")

    return name
