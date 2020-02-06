"""
Ralph tracking logs filters.
"""


def anonymous(events):
    """Remove anonymous events.

    Args:
        events (DataFrame): events to filter

    Returns:
        Filtered pandas DataFrame.

    """
    return events.loc[lambda df: df["username"] != "", :]
