"""
Ralph exceptions.
"""


class BackendException(Exception):
    """Raised when a backend has a failure."""


class BackendParameterException(Exception):
    """Raised when a backend parameter value is not valid."""


class ConfigurationException(Exception):
    """Raised when the configuration is not valid."""


class EventKeyError(Exception):
    """Raised when an expected event key has not been found."""


class UnsupportedBackendException(Exception):
    """Raised when trying to use an unsupported backend type."""


class ModelRulesException(Exception):
    """Raised when a model rules list is a subset or superset of another model rules list"""
