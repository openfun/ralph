"""Tests for Ralph base HTTP backend."""

from typing import Iterator, Union

from ralph.backends.http.base import BaseHTTPBackend, BaseQuery


def test_backends_http_base_abstract_interface_with_implemented_abstract_method():
    """Tests the interface mechanism with properly implemented abstract methods."""

    class GoodStorage(BaseHTTPBackend):
        """Correct implementation with required abstract methods."""

        name = "good"

        async def status(self):
            """Fakes the status method."""

        async def list(
            self, target: str = None, details: bool = False, new: bool = False
        ) -> Iterator[Union[str, dict]]:
            """Fakes the list method."""

        async def read(self):  # pylint: disable=arguments-differ
            """Fakes the read method."""

        async def write(self):  # pylint: disable=arguments-differ
            """Fakes the write method."""

    GoodStorage()

    assert GoodStorage.name == "good"
    assert GoodStorage.query == BaseQuery
