"""
Ralph exceptions.
"""


class BackendParameterException(Exception):
    """Raised when a backend parameter value is not valid"""


class EventKeyError(Exception):
    """Raised when an expected event key has not been found."""
