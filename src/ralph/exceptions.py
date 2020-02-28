"""
Ralph exceptions.
"""


# --- Parsers
class EventKeyError(Exception):
    """Raised when an expected event key has not been found during tracking log parsing."""


class BadlyFormattedEvent(Exception):
    """Raised when an event does not comply with expected event data."""


class IgnoredEvent(Exception):
    """Raised when an event is explicitly ignored."""


# --- Formatters
class NotImplementedStatementType(Exception):
    """Raised when a statement type formatter is not implemented."""
