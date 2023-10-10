"""ClickHouse LRS backend for Ralph."""

import logging
from typing import Iterator, List

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
from ralph.exceptions import BackendException, BackendParameterException

logger = logging.getLogger(__name__)


class ClickHouseLRSBackendSettings(
    BaseLRSBackendSettings, ClickHouseDataBackendSettings
):
    """Represent the ClickHouse data backend default configuration.

    Attributes:
        IDS_CHUNK_SIZE (int): The chunk size for querying by ids.
    """

    IDS_CHUNK_SIZE: int = 10000


class ClickHouseLRSBackend(BaseLRSBackend, ClickHouseDataBackend):
    """ClickHouse LRS backend implementation."""

    settings_class = ClickHouseLRSBackendSettings

    def query_statements(self, params: RalphStatementsQuery) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""
        ch_params = params.dict(exclude_none=True)
        where = []

        if params.statement_id:
            where.append("event_id = {statementId:UUID}")

        self._add_agent_filters(ch_params, where, params.agent, "actor")
        ch_params.pop("agent", None)

        self._add_agent_filters(ch_params, where, params.authority, "authority")
        ch_params.pop("authority", None)

        if params.verb:
            where.append("event.verb.id = {verb:String}")

        if params.activity:
            where.append("event.object.objectType = 'Activity'")
            where.append("event.object.id = {activity:String}")

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

        query = {
            "select": ["event_id", "emission_time", "event"],
            "where": where,
            "parameters": ch_params,
            "limit": params.limit,
            "sort": order_by,
        }
        try:
            clickhouse_response = list(
                self.read(
                    query=query,
                    target=self.event_table_name,
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

    def query_statements_by_ids(self, ids: List[str]) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""

        def chunk_id_list(chunk_size=self.settings.IDS_CHUNK_SIZE):
            for i in range(0, len(ids), chunk_size):
                yield ids[i : i + chunk_size]

        query = {
            "select": "event",
            "where": "event_id IN ({ids:Array(String)})",
            "parameters": {"ids": ["1"]},
            "column_oriented": True,
        }
        try:
            for chunk_ids in chunk_id_list():
                query["parameters"]["ids"] = chunk_ids
                for raw in self.read(
                    query=query,
                    target=self.event_table_name,
                    ignore_errors=True,
                ):
                    yield raw["event"]
        except (BackendException, BackendParameterException) as error:
            msg = "Failed to read from ClickHouse"
            logger.error(msg)
            raise error

    @staticmethod
    def _add_agent_filters(
        ch_params: dict,
        where: list,
        agent_params: AgentParameters,
        target_field: str,
    ):
        """Add filters relative to agents to `where`."""
        if not agent_params:
            return
        if not isinstance(agent_params, dict):
            agent_params = agent_params.dict()
        if agent_params.get("mbox"):
            ch_params[f"{target_field}__mbox"] = agent_params.get("mbox")
            where.append(f"event.{target_field}.mbox = {{{target_field}__mbox:String}}")
        elif agent_params.get("mbox_sha1sum"):
            ch_params[f"{target_field}__mbox_sha1sum"] = agent_params.get(
                "mbox_sha1sum"
            )
            where.append(
                f"event.{target_field}.mbox_sha1sum = {{{target_field}__mbox_sha1sum:String}}"  # noqa: E501 # pylint: disable=line-too-long
            )
        elif agent_params.get("openid"):
            ch_params[f"{target_field}__openid"] = agent_params.get("openid")
            where.append(
                f"event.{target_field}.openid = {{{target_field}__openid:String}}"
            )
        elif agent_params.get("account__name"):
            ch_params[f"{target_field}__account__name"] = agent_params.get(
                "account__name"
            )
            where.append(
                f"event.{target_field}.account.name = {{{target_field}__account__name:String}}"  # noqa: E501 # pylint: disable=line-too-long
            )
            ch_params[f"{target_field}__account_home_page"] = agent_params.get(
                "account__home_page"
            )
            where.append(
                f"event.{target_field}.account.homePage = {{{target_field}__account_home_page:String}}"  # noqa: E501 # pylint: disable=line-too-long
            )
