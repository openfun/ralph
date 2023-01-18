"""xAPI statement forwarding background task."""

import logging
from functools import lru_cache
from typing import List

from httpx import AsyncClient, AsyncHTTPTransport, HTTPStatusError, RequestError

from ..conf import XapiForwardingConfigurationSettings, settings

logger = logging.getLogger(__name__)


@lru_cache
def get_active_xapi_forwardings() -> List[XapiForwardingConfigurationSettings]:
    """Returns a list of active xAPI forwarding configuration settings."""
    active_forwardings = []
    if not settings.XAPI_FORWARDINGS:
        logger.info("No xAPI forwarding configured; forwarding is disabled.")
        return active_forwardings

    for forwarding in settings.XAPI_FORWARDINGS:
        if forwarding.is_active:
            active_forwardings.append(forwarding)
            continue
        msg = (
            "The RALPH_XAPI_FORWARDINGS configuration value: '%s' is not active. "
            "It will be ignored."
        )
        logger.info(msg, forwarding)

    return active_forwardings


async def forward_xapi_statements(statements: List[dict]):
    """Forwards xAPI statements."""
    for forwarding in get_active_xapi_forwardings():
        transport = AsyncHTTPTransport(retries=forwarding.max_retries)
        async with AsyncClient(transport=transport) as client:
            try:
                req = await client.post(
                    forwarding.url,
                    json=statements,
                    auth=(forwarding.basic_username, forwarding.basic_password),
                    timeout=forwarding.timeout,
                )
                req.raise_for_status()
                msg = "Forwarded %s statements to %s with success."
                logger.debug(msg, len(statements), forwarding.url)
            except (RequestError, HTTPStatusError) as error:
                logger.error("Failed to forward xAPI statements. %s", error)
