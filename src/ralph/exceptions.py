"""
Ralph exceptions.
"""


class BackendException(Exception):
    """Raised when a backend has a failure."""


class BackendParameterException(Exception):
    """Raised when a backend parameter value is not valid."""


class BadFormatException(Exception):
    """Raised when the format of an event is not valid."""


class ConfigurationException(Exception):
    """Raised when the configuration is not valid."""


class ConversionException(Exception):
    """Raised when a converter has a failure."""


class EventKeyError(Exception):
    """Raised when an expected event key has not been found."""


class MissingConversionSetException(Exception):
    """Raised when an expected conversion set has not been found."""


class UnknownEventException(Exception):
    """Raised when no pydantic model is found for a given event."""


class UnsupportedBackendException(Exception):
    """Raised when trying to use an unsupported backend type."""


class ModelRulesException(Exception):
    """Raised when a model rules list is a subset or superset of another model rules list"""
