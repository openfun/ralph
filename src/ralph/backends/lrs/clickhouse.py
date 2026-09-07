"""ClickHouse LRS backend for Ralph."""

import logging
from functools import reduce
from typing import Generator, Iterator, List, Optional, Union

from pydantic_settings import SettingsConfigDict

from ralph.backends.data.clickhouse import (
    ClickHouseDataBackend,
    ClickHouseDataBackendSettings,
)
from ralph.backends.lrs.base import (
    AgentParameters,
    BaseLRSBackend,
    BaseLRSBackendSettings,
    RalphStatementsQuery,
    StatementQueryResult,
)
from ralph.conf import BASE_SETTINGS_CONFIG
from ralph.exceptions import BackendException, BackendParameterException

logger = logging.getLogger(__name__)


class ClickHouseLRSBackendSettings(
    BaseLRSBackendSettings, ClickHouseDataBackendSettings
):
    """ClickHouse LRS backend default configuration.

    Attributes:
        IDS_CHUNK_SIZE (int): The chunk size for querying by ids.
    """

    model_config = {
        **BASE_SETTINGS_CONFIG,
        **SettingsConfigDict(env_prefix="RALPH_BACKENDS__LRS__CLICKHOUSE__"),
    }

    IDS_CHUNK_SIZE: int = 10000


class ClickHouseLRSBackend(
    BaseLRSBackend[ClickHouseLRSBackendSettings], ClickHouseDataBackend
):
    """ClickHouse LRS backend implementation."""

    def query_statements(
        self, params: RalphStatementsQuery, target: Optional[str] = None
    ) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""
        ch_params = params.model_dump(exclude_none=True)

        if "statement_id" in ch_params:
            ch_params["statementId"] = ch_params["statement_id"]

        where = []

        if params.statement_id:
            where.append("event_id = {statementId:UUID}")

        self._add_agent_filters(ch_params, where, params.agent, "actor")
        ch_params.pop("agent", None)

        self._add_agent_filters(ch_params, where, params.authority, "authority")
        ch_params.pop("authority", None)

        if params.verb:
            where.append("JSONExtractString(event, 'verb', 'id') = {verb:String}")

        if params.activity:
            where.append("JSONExtractString(event, 'object', 'id') = {activity:String}")

        if params.since:
            where.append("emission_time > {since:DateTime64(6)}")

        if params.until:
            where.append("emission_time <= {until:DateTime64(6)}")

        if params.search_after:
            search_order = ">" if params.ascending else "<"

            where.append(
                f"(emission_time {search_order} "
                "{search_after:DateTime64(6)}"
                " OR "
                "(emission_time = {search_after:DateTime64(6)}"
                " AND "
                f"event_id {search_order} "
                "{pit_id:UUID}"
                "))"
            )

        sort_order = "ASCENDING" if params.ascending else "DESCENDING"
        order_by = f"emission_time {sort_order}, event_id {sort_order}"

        query = self.query_class(
            select=["event_id", "emission_time", "event"],
            where=where,
            parameters=ch_params,
            limit=params.limit,
            sort=order_by,
        )

        try:
            clickhouse_response = list(
                self.read(
                    query=query,
                    target=target,
                    ignore_errors=True,
                )
            )
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from ClickHouse")
            raise error

        new_search_after = None
        new_pit_id = None

        if clickhouse_response:
            # Our search after string is a combination of event timestamp and
            # event id, so that we can avoid losing events when they have the
            # same timestamp, and also avoid sending the same event twice.
            new_search_after = clickhouse_response[-1]["emission_time"].isoformat()
            new_pit_id = str(clickhouse_response[-1]["event_id"])

        return StatementQueryResult(
            statements=[document["event"] for document in clickhouse_response],
            search_after=new_search_after,
            pit_id=new_pit_id,
        )

    def query_statements_by_ids(
        self, ids: List[str], target: Optional[str] = None
    ) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""

        def chunk_id_list(chunk_size: int = self.settings.IDS_CHUNK_SIZE) -> Generator:
            for i in range(0, len(ids), chunk_size):
                yield ids[i : i + chunk_size]

        query = self.query_class(
            select="event",
            where="event_id IN ({ids:Array(String)})",
            parameters={"ids": ["1"]},
            column_oriented=True,
        )
        try:
            for chunk_ids in chunk_id_list():
                query.parameters["ids"] = chunk_ids
                ch_response = self.read(
                    query=query,
                    target=target,
                    ignore_errors=True,
                )
                yield from (document["event"] for document in ch_response)
        except (BackendException, BackendParameterException) as error:
            msg = "Failed to read from ClickHouse"
            logger.error(msg)
            raise error

    @staticmethod
    def _get_agent_filters(
        agent_params: AgentParameters,
        target_field: str,
        idx: Optional[int] = None,
    ) -> Union[tuple[list[str], dict], None]:
        if not agent_params:
            return None

        if not isinstance(agent_params, dict):
            agent_params = agent_params.model_dump()

        extract_string_field = f"'{target_field}'"
        param_field = f"{target_field}_{idx}" if idx is not None else target_field

        if agent_params.get("mbox"):
            return (
                [
                    f"JSONExtractString(event, {extract_string_field}, 'mbox') = "
                    f"{{{param_field}__mbox:String}}"
                ],
                {f"{param_field}__mbox": agent_params.get("mbox")},
            )
        elif agent_params.get("mbox_sha1sum"):
            return (
                [
                    f"JSONExtractString(event, {extract_string_field},"
                    f" 'mbox_sha1sum') = "
                    f"{{{param_field}__mbox_sha1sum:String}}"
                ],
                {f"{param_field}__mbox_sha1sum": agent_params.get("mbox_sha1sum")},
            )
        elif agent_params.get("openid"):
            return (
                [
                    f"JSONExtractString(event, {extract_string_field}, 'openid') = "
                    f"{{{param_field}__openid:String}}"
                ],
                {f"{param_field}__openid": agent_params.get("openid")},
            )
        elif agent_params.get("account__name"):
            return (
                [
                    f"JSONExtractString(event, {extract_string_field}, 'account',"
                    f" 'name') = "
                    f"{{{param_field}__account__name:String}}",
                    f"JSONExtractString(event, {extract_string_field}, 'account',"
                    f" 'homePage') = "
                    f"{{{param_field}__account__home_page:String}}",
                ],
                {
                    f"{param_field}__account__name": agent_params.get("account__name"),
                    f"{param_field}__account__home_page": agent_params.get(
                        "account__home_page"
                    ),
                },
            )

    @classmethod
    def _add_agent_filters(
        cls,
        ch_params: dict,
        where: list,
        agent_params: Union[AgentParameters, list[AgentParameters]],
        target_field: str,
    ) -> None:
        """Add filters relative to agents to `where`."""
        if not agent_params:
            return
        elif not isinstance(agent_params, list):
            filters = cls._get_agent_filters(
                agent_params=agent_params, target_field=target_field
            )
            if filters:
                _where, _ch_params = filters
                ch_params.update(_ch_params)
                where.extend(_where)
        else:
            filters = [
                cls._get_agent_filters(
                    agent_params=params, target_field=target_field, idx=idx
                )
                for idx, params in enumerate(agent_params)
                if params
            ]
            _ch_params = reduce(lambda acc, el: acc | el[1], filters, {})
            _where = [" OR ".join([" AND ".join(el[0]) for el in filters])]
            ch_params.update(_ch_params)
            where.extend(_where)
