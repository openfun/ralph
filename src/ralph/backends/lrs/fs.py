"""FileSystem LRS backend for Ralph."""

import logging
from datetime import datetime
from io import IOBase
from typing import Iterable, List, Literal, Optional, Union
from uuid import UUID

from ralph.backends.data.base import BaseOperationType, BaseSettingsConfig
from ralph.backends.data.fs import FSDataBackend, FSDataBackendSettings
from ralph.backends.lrs.base import (
    AgentParameters,
    BaseLRSBackend,
    BaseLRSBackendSettings,
    RalphStatementsQuery,
    StatementQueryResult,
)

logger = logging.getLogger(__name__)


class FSLRSBackendSettings(BaseLRSBackendSettings, FSDataBackendSettings):
    """FileSystem LRS backend default configuration.

    Attributes:
        DEFAULT_LRS_FILE (str): The default LRS filename to store statements.
    """

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__LRS__FS__"

    DEFAULT_LRS_FILE: str = "fs_lrs.jsonl"


class FSLRSBackend(BaseLRSBackend, FSDataBackend):
    """FileSystem LRS Backend."""

    settings_class = FSLRSBackendSettings

    def write(  # noqa: PLR0913
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Union[None, str] = None,
        chunk_size: Union[None, int] = None,
        ignore_errors: bool = False,
        operation_type: Union[None, BaseOperationType] = None,
    ) -> int:
        """Write data records to the target file and return their count.

        See `FSDataBackend.write`.
        """
        target = target if target else self.settings.DEFAULT_LRS_FILE
        return super().write(data, target, chunk_size, ignore_errors, operation_type)

    def query_statements(self, params: RalphStatementsQuery) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""
        filters = []
        self._add_filter_by_id(filters, params.statement_id)
        self._add_filter_by_agent(filters, params.agent, params.related_agents)
        self._add_filter_by_authority(filters, params.authority)
        self._add_filter_by_verb(filters, params.verb)
        self._add_filter_by_activity(
            filters, params.activity, params.related_activities
        )
        self._add_filter_by_registration(filters, params.registration)
        self._add_filter_by_timestamp_since(filters, params.since)
        self._add_filter_by_timestamp_until(filters, params.until)
        self._add_filter_by_search_after(filters, params.search_after)

        limit = params.limit
        statements_count = 0
        search_after = None
        statements = []
        for statement in self.read(query=self.settings.DEFAULT_LRS_FILE):
            for query_filter in filters:
                if not query_filter(statement):
                    break
            else:
                statements.append(statement)
                statements_count += 1
                if limit and statements_count == limit:
                    search_after = statements[-1].get("id")
                    break

        if params.ascending:
            statements.reverse()
        return StatementQueryResult(
            statements=statements,
            pit_id=None,
            search_after=search_after,
        )

    def query_statements_by_ids(self, ids: List[str]) -> List:
        """Return the list of matching statement IDs from the database."""
        statement_ids = set(ids)
        statements = []
        for statement in self.read(query=self.settings.DEFAULT_LRS_FILE):
            if statement.get("id") in statement_ids:
                statements.append(statement)

        return statements

    @staticmethod
    def _add_filter_by_agent(
        filters: list, agent: Optional[AgentParameters], related: Optional[bool]
    ) -> None:
        """Add agent filters to `filters` if `agent` is set."""
        if not agent:
            return

        if not isinstance(agent, dict):
            agent = agent.dict()
        FSLRSBackend._add_filter_by_mbox(filters, agent.get("mbox", None), related)
        FSLRSBackend._add_filter_by_sha1sum(
            filters, agent.get("mbox_sha1sum", None), related
        )
        FSLRSBackend._add_filter_by_openid(filters, agent.get("openid", None), related)
        FSLRSBackend._add_filter_by_account(
            filters,
            agent.get("account__name", None),
            agent.get("account__home_page", None),
            related,
        )

    @staticmethod
    def _add_filter_by_authority(
        filters: list,
        authority: Optional[AgentParameters],
    ) -> None:
        """Add authority filters to `filters` if `authority` is set."""
        if not authority:
            return

        if not isinstance(authority, dict):
            authority = authority.dict()
        FSLRSBackend._add_filter_by_mbox(
            filters, authority.get("mbox", None), field="authority"
        )
        FSLRSBackend._add_filter_by_sha1sum(
            filters, authority.get("mbox_sha1sum", None), field="authority"
        )
        FSLRSBackend._add_filter_by_openid(
            filters, authority.get("openid", None), field="authority"
        )
        FSLRSBackend._add_filter_by_account(
            filters,
            authority.get("account__name", None),
            authority.get("account__home_page", None),
            field="authority",
        )

    @staticmethod
    def _add_filter_by_id(filters: list, statement_id: Optional[str]) -> None:
        """Add the `match_statement_id` filter if `statement_id` is set."""

        def match_statement_id(statement: dict) -> bool:
            """Return `True` if the statement has the given `statement_id`."""
            return statement.get("id") == statement_id

        if statement_id:
            filters.append(match_statement_id)

    @staticmethod
    def _get_related_agents(statement: dict) -> Iterable[dict]:
        yield statement.get("actor", {})
        yield statement.get("object", {})
        yield statement.get("authority", {})
        context = statement.get("context", {})
        yield context.get("instructor", {})
        yield context.get("team", {})

    @staticmethod
    def _add_filter_by_mbox(
        filters: list,
        mbox: Optional[str],
        related: Optional[bool] = False,
        field: Literal["actor", "authority"] = "actor",
    ) -> None:
        """Add the `match_mbox` filter if `mbox` is set."""

        def match_mbox(statement: dict) -> bool:
            """Return `True` if the statement has the given `actor.mbox`."""
            return statement.get(field, {}).get("mbox") == mbox

        def match_related_mbox(statement: dict) -> bool:
            """Return `True` if the statement has any agent matching `mbox`."""
            for agent in FSLRSBackend._get_related_agents(statement):
                if agent.get("mbox") == mbox:
                    return True

            statement_object = statement.get("object", {})
            if statement_object.get("objectType") == "SubStatement":
                return match_related_mbox(statement_object)
            return False

        if mbox:
            filters.append(match_related_mbox if related else match_mbox)

    @staticmethod
    def _add_filter_by_sha1sum(
        filters: list,
        sha1sum: Optional[str],
        related: Optional[bool] = False,
        field: Literal["actor", "authority"] = "actor",
    ) -> None:
        """Add the `match_sha1sum` filter if `sha1sum` is set."""

        def match_sha1sum(statement: dict) -> bool:
            """Return `True` if the statement has the given `actor.sha1sum`."""
            return statement.get(field, {}).get("mbox_sha1sum") == sha1sum

        def match_related_sha1sum(statement: dict) -> bool:
            """Return `True` if the statement has any agent matching `sha1sum`."""
            for agent in FSLRSBackend._get_related_agents(statement):
                if agent.get("mbox_sha1sum") == sha1sum:
                    return True

            statement_object = statement.get("object", {})
            if statement_object.get("objectType") == "SubStatement":
                return match_related_sha1sum(statement_object)
            return False

        if sha1sum:
            filters.append(match_related_sha1sum if related else match_sha1sum)

    @staticmethod
    def _add_filter_by_openid(
        filters: list,
        openid: Optional[str],
        related: Optional[bool] = False,
        field: Literal["actor", "authority"] = "actor",
    ) -> None:
        """Add the `match_openid` filter if `openid` is set."""

        def match_openid(statement: dict) -> bool:
            """Return `True` if the statement has the given `actor.openid`."""
            return statement.get(field, {}).get("openid") == openid

        def match_related_openid(statement: dict) -> bool:
            """Return `True` if the statement has any agent matching `openid`."""
            for agent in FSLRSBackend._get_related_agents(statement):
                if agent.get("openid") == openid:
                    return True

            statement_object = statement.get("object", {})
            if statement_object.get("objectType") == "SubStatement":
                return match_related_openid(statement_object)
            return False

        if openid:
            filters.append(match_related_openid if related else match_openid)

    @staticmethod
    def _add_filter_by_account(
        filters: list,
        name: Optional[str],
        home_page: Optional[str],
        related: Optional[bool] = False,
        field: Literal["actor", "authority"] = "actor",
    ) -> None:
        """Add the `match_account` filter if `name` or `home_page` is set."""

        def match_account(statement: dict) -> bool:
            """Return `True` if the statement has the given `actor.account`."""
            account = statement.get(field, {}).get("account", {})
            return account.get("name") == name and account.get("homePage") == home_page

        def match_related_account(statement: dict) -> bool:
            """Return `True` if the statement has any agent matching the account."""
            for agent in FSLRSBackend._get_related_agents(statement):
                account = agent.get("account", {})
                if account.get("name") == name and account.get("homePage") == home_page:
                    return True

            statement_object = statement.get("object", {})
            if statement_object.get("objectType") == "SubStatement":
                return match_related_account(statement_object)
            return False

        if name and home_page:
            filters.append(match_related_account if related else match_account)

    @staticmethod
    def _add_filter_by_verb(filters: list, verb_id: Optional[str]) -> None:
        """Add the `match_verb_id` filter if `verb_id` is set."""

        def match_verb_id(statement: dict) -> bool:
            """Return `True` if the statement has the given `verb.id`."""
            return statement.get("verb", {}).get("id") == verb_id

        if verb_id:
            filters.append(match_verb_id)

    @staticmethod
    def _add_filter_by_activity(
        filters: list, object_id: Optional[str], related: Optional[bool]
    ) -> None:
        """Add the `match_object_id` filter if `object_id` is set."""

        def match_object_id(statement: dict) -> bool:
            """Return `True` if the statement has the given `object.id`."""
            return statement.get("object", {}).get("id") == object_id

        def match_related_object_id(statement: dict) -> bool:
            """Return `True` if the statement has any object.id matching `object_id`."""
            statement_object = statement.get("object", {})
            if statement_object.get("id") == object_id:
                return True
            activities = statement.get("context", {}).get("contextActivities", {})
            for activity in activities.values():
                if isinstance(activity, dict):
                    if activity.get("id") == object_id:
                        return True
                else:
                    for sub_activity in activity:
                        if sub_activity.get("id") == object_id:
                            return True
            if statement_object.get("objectType") == "SubStatement":
                return match_related_object_id(statement_object)

            return False

        if object_id:
            filters.append(match_related_object_id if related else match_object_id)

    @staticmethod
    def _add_filter_by_timestamp_since(
        filters: list, timestamp: Optional[datetime]
    ) -> None:
        """Add the `match_since` filter if `timestamp` is set."""
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        def match_since(statement: dict) -> bool:
            """Return `True` if the statement was created after `timestamp`."""
            try:
                statement_timestamp = datetime.fromisoformat(statement.get("timestamp"))
            except (TypeError, ValueError) as error:
                msg = "Statement with id=%s contains unparsable timestamp=%s"
                logger.debug(msg, statement.get("id"), error)
                return False
            return statement_timestamp > timestamp

        if timestamp:
            filters.append(match_since)

    @staticmethod
    def _add_filter_by_timestamp_until(
        filters: list, timestamp: Optional[datetime]
    ) -> None:
        """Add the `match_until` function if `timestamp` is set."""
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        def match_until(statement: dict) -> bool:
            """Return `True` if the statement was created before `timestamp`."""
            try:
                statement_timestamp = datetime.fromisoformat(statement.get("timestamp"))
            except (TypeError, ValueError) as error:
                msg = "Statement with id=%s contains unparsable timestamp=%s"
                logger.debug(msg, statement.get("id"), error)
                return False
            return statement_timestamp <= timestamp

        if timestamp:
            filters.append(match_until)

    @staticmethod
    def _add_filter_by_search_after(filters: list, search_after: Optional[str]) -> None:
        """Add the `match_search_after` filter if `search_after` is set."""
        search_after_state = {"state": False}

        def match_search_after(statement: dict) -> bool:
            """Return `True` if the statement was created after `search_after`."""
            if search_after_state["state"]:
                return True
            if statement.get("id") == search_after:
                search_after_state["state"] = True
            return False

        if search_after:
            filters.append(match_search_after)

    @staticmethod
    def _add_filter_by_registration(
        filters: list, registration: Optional[UUID]
    ) -> None:
        """Add the `match_registration` filter if `registration` is set."""
        registration_str = str(registration)

        def match_registration(statement: dict) -> bool:
            """Return `True` if the statement has the given `context.registration`."""
            return statement.get("context", {}).get("registration") == registration_str

        if registration:
            filters.append(match_registration)
