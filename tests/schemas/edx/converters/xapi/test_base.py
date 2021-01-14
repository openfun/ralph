"""Tests for the BaseXapiConverter class"""

import pytest

from ralph.schemas.edx.converters.xapi.base import BaseXapiConverter

PLATFORM = "https://fun-mooc.fr"


class BadBaseXapiConverter(BaseXapiConverter):
    """Missing verb property definition"""

    @property
    def object(self):
        return {}


def test_object_property_raises_exception():
    """Test that when accessing object property we get a NotImplementedError"""

    error_message = "BaseXapiConverter class should implement the object property"
    with pytest.raises(NotImplementedError, match=error_message):
        BaseXapiConverter(PLATFORM)


def test_verb_property_raises_exception():
    """Test that when accessing verb property we get a NotImplementedError"""

    error_message = "BadBaseXapiConverter class should implement the verb property"
    with pytest.raises(NotImplementedError, match=error_message):
        BadBaseXapiConverter(PLATFORM)
