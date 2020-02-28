"""
Ralph tracking logs transformers.
"""
import pandas as pd

from .exceptions import EventKeyError


def datetime(events):
    """Convert event time field string to a python datetime instance.

    Args:
        events (DataFrame): events to modify

    Returns:
        Modified pandas DataFrame.

    """
    if events.get("time", None) is None:
        raise EventKeyError(
            "Cannot convert time column to datetime instances, column not found."
        )

    events["time"] = pd.to_datetime(events["time"])
    return events
