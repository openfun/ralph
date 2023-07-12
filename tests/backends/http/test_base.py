"""Tests for Ralph base HTTP backend."""

from typing import Iterator, List, Union

from ralph.backends.http.base import BaseHTTP, BaseQuery, OperationType


def test_backends_http_base_abstract_interface_with_implemented_abstract_method():
    """Tests the interface mechanism with properly implemented abstract methods."""

    class GoodStorage(BaseHTTP):
        """Correct implementation with required abstract methods."""

        name = "good"

        async def status(self):
            """Fakes the status method."""

        async def list(
            self, target: str = None, details: bool = False, new: bool = False
        ) -> Iterator[Union[str, dict]]:
            """Fakes the list method."""

        async def read(  # pylint: disable=too-many-arguments
            self,
            query: Union[str, BaseQuery] = None,
            target: str = None,
            chunk_size: Union[None, int] = None,
            raw_output: bool = False,
            ignore_errors: bool = False,
        ):
            """Fakes the read method."""

        async def write(  # pylint: disable=too-many-arguments
            self,
            data: Union[List[bytes], List[dict]],
            target: Union[None, str] = None,
            chunk_size: Union[None, int] = 500,
            ignore_errors: bool = False,
            operation_type: Union[None, OperationType] = None,
        ):
            """Fakes the write method."""

    GoodStorage()

    assert GoodStorage.name == "good"
    assert GoodStorage.query == BaseQuery
