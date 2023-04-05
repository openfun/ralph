"""LRS HTTP backend for Ralph."""

import logging
import json
from typing import Iterable, Union, Iterator
from urllib.parse import urlparse
from more_itertools import chunked

from httpx import AsyncClient, Headers
from pydantic import HttpUrl

from ralph.conf import settings
from ralph.exceptions import BackendException

from .base import BaseHTTP

#lrs_settings = settings.BACKENDS.HTTP.LRS
logger = logging.getLogger(__name__)


class LRSHTTP(BaseHTTP):
    """LRS HTTP backend."""
    name = "lrs"

    def __init__(
        self,
        connection_url: HttpUrl,
        headers: Headers = None,
    ):
        """Instantiates the LRS client, using Basic Auth.
        Args:
            connection_url (HttpUrl): Connection URL to a LRS using Basic Auth.
            headers (json): Headers defined for the LRS server connection
        """
        
        # Parse basic auth credentials
        if connection_url.user and connection_url.password:
            self.auth = (connection_url.user, connection_url.password)
        else:
            raise ValueError(
                            "The `connection_url` should be formated so as to allow basic auth. ",
                            "For example: http://username:password@example.com/ ."
                            "The value received was: %s .", connection_url
                            )
        
        self.headers = headers

    def _raise_for_status(self, response):
        """Raise custom BackendException for error in HTTP server."""
        try:
            response.raise_for_status()
        except Exception as error:
            msg = "Failed to fetch statements."
            logger.error("%s. %s", msg, error)
            raise BackendException(msg, *error.args) from error

    def async_get_statements(self, target: str) -> Iterator[dict]:
        """Get statements asynchronously from LRS.
        The `get` method defined in the LRS spefication returns `statements` array and
        `more` IRL. This method returns an asynchronous generator of statements."""

        origin = urlparse(target).scheme + "://" + urlparse(target).netloc

        async def fetch_statements(url, origin=origin):
            async with AsyncClient(auth=self.auth, headers=self.headers) as client:
                response = await client.get(url=url)
                self._raise_for_status(response)
                statements = response.json()["statements"]
                for statement in statements:
                    yield statement

                if "more" in response.json() and response.json()["more"]:
                    # yield from is not authorized in async function
                    async for statement in fetch_statements(origin + response.json()["more"]):
                        yield statement 

        return fetch_statements(target)

    async def async_post_statements(
        self,
        target: str,
        data: Union[dict, Iterable[dict]],
        chunk_size: Union[None, int] = None,
    ) -> int:
        """Post statements asynchronously to LRS asynchronously.
        Stores in an LRS a statement or a set of statements. Returns a list of responses."""

        num_requests = 0
        
        if isinstance(data, dict):
            data = [data]

        if chunk_size is None:
            chunks = [data]
        else:
            chunks = chunked(data, chunk_size)
        
        async with AsyncClient(auth=self.auth, headers=self.headers) as client:
            for chunk in chunks:
                # Encode data to allow async post
                response = await client.post(target, data=json.dumps(list(chunk)).encode('utf-8')) 
                self._raise_for_status(response)
                num_requests += 1
                logger.debug("Made %d POST requests", num_requests)

        return num_requests
    
        
