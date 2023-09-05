"""Tests for the base xAPI Converter."""

from uuid import UUID

import pytest

from ralph.exceptions import ConfigurationException
from ralph.models.edx.converters.xapi.base import BaseXapiConverter


@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_models_edx_converters_xapi_base_xapi_converter_successful_initialization(
    uuid_namespace,
):
    """Test BaseXapiConverter initialization."""

    class DummyBaseXapiConverter(BaseXapiConverter):
        """Dummy implementation of abstract BaseXapiConverter."""

        def _get_conversion_items(self):  # pylint: disable=no-self-use
            """Returns a set of ConversionItems used for conversion."""
            return set()

    converter = DummyBaseXapiConverter(uuid_namespace, "https://fun-mooc.fr")
    assert converter.platform_url == "https://fun-mooc.fr"
    assert converter.uuid_namespace == UUID(uuid_namespace)


def test_models_edx_converters_xapi_base_xapi_converter_unsuccessful_initialization():
    """Tests BaseXapiConverter failed initialization."""

    class DummyBaseXapiConverter(BaseXapiConverter):
        """Dummy implementation of abstract BaseXapiConverter."""

        def _get_conversion_items(self):  # pylint: disable=no-self-use
            """Returns a set of ConversionItems used for conversion."""
            return set()

    with pytest.raises(ConfigurationException, match="Invalid UUID namespace"):
        DummyBaseXapiConverter(None, "https://fun-mooc.fr")
