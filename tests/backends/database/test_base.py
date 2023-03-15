"""Tests for Ralph base database backend."""

from ralph.backends.database.base import BaseAsyncDatabase, BaseDatabase


def test_backends_database_base_abstract_interface_with_abstract_method():
    """Tests the interface mechanism with properly implemented abstract methods."""

    class GoodDatabase(BaseDatabase):
        """Correct implementation with required abstract methods."""

        name = "good"

        def status(self):
            """Fakes the status method."""

        def get(self, query=None, chunk_size=0):
            """Fakes the get method."""

        def put(self, stream, chunk_size=0, ignore_errors=False):
            """Fakes the put method."""

        def query_statements(self, params):
            """Fakes the query_statements method."""

        def query_statements_by_ids(self, ids):
            """Fakes the query_statements_by_ids method."""

    GoodDatabase()

    assert GoodDatabase.name == "good"


# pylint: disable=line-too-long
def test_backends_database_async_base_abstract_interface_with_abstract_method():
    """Tests the interface mechanism with implemented abstract async methods."""

    class GoodAsyncDatabase(BaseAsyncDatabase):
        """Correct implementation with required abstract methods."""

        name = "good"

        async def status(self):
            """Fakes the status method."""

        async def get(self, query=None, chunk_size=0):
            """Fakes the get method."""

        async def put(self, stream, chunk_size=0, ignore_errors=False):
            """Fakes the put method."""

        async def query_statements(self, params):
            """Fakes the query_statements method."""

        async def query_statements_by_ids(self, ids):
            """Fakes the query_statements_by_ids method."""

        async def close(self):
            """Fakes the close method."""

    GoodAsyncDatabase()

    assert GoodAsyncDatabase.name == "good"
