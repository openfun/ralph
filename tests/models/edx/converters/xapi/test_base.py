"""Tests for the base xAPI Converter"""

from ralph.models.edx.converters.xapi.base import BaseXapiConverter


class DummyBaseXapiConverter(BaseXapiConverter):
    """Dummy implementation of abstract BaseXapiConverter."""

    def get_conversion_set(self):  # pylint: disable=no-self-use
        """Returns a conversion set used for conversion."""

        return set()


def test_models_edx_converters_xapi_base_base_xapi_converter_successful_initialization():
    """Tests BaseXapiConverter initialization."""

    converter = DummyBaseXapiConverter("https://fun-mooc.fr")
    assert converter.platform == "https://fun-mooc.fr"
