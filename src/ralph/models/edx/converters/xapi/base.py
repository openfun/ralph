"""Base xAPI Converter"""

from ralph.models.converter import BaseConverter


class BaseXapiConverter(BaseConverter):
    """Base xAPI Converter."""

    def __init__(self, platform):
        """Initializes BaseXapiConverter."""

        self.platform = platform
        super().__init__()
