"""API routes related to statements."""

import logging
from datetime import datetime
from typing import List, Literal, Optional, Union
from urllib.parse import ParseResult, urlencode
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)
from pydantic import parse_raw_as
from pydantic.types import Json

from ralph.api.forwarding import forward_xapi_statements, get_active_xapi_forwardings
from ralph.backends.database.base import (
    AgentParameters,
    BaseDatabase,
    StatementParameters,
)
from ralph.conf import settings
from ralph.exceptions import BackendException, BadFormatException
from ralph.models.xapi.base.agents import (
    BaseXapiAgent,
    BaseXapiAgentWithAccount,
    BaseXapiAgentWithMbox,
    BaseXapiAgentWithMboxSha1Sum,
    BaseXapiAgentWithOpenId,
)

from ..auth import authenticated_user
from ..models import ErrorDetail, LaxStatement

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/xAPI/statements",
    dependencies=[Depends(authenticated_user)],
)


DATABASE_CLIENT: BaseDatabase = getattr(
    settings.BACKENDS.DATABASE, settings.RUNSERVER_BACKEND.upper()
).get_instance()

POST_PUT_RESPONSES = {
    400: {
        "model": ErrorDetail,
        "description": "The request was invalid.",
    },
    409: {
        "model": ErrorDetail,
        "description": "Statements had a conflict with existing statements.",
    },
}


@router.get("")
@router.get("/")
# pylint: disable=too-many-arguments, too-many-locals
async def get(
    request: Request,
    ###
    # Query string parameters defined by the LRS specification
    ###
    # pylint: disable=invalid-name
    statementId: Optional[str] = Query(None, description="Id of Statement to fetch"),
    # pylint: disable=invalid-name, unused-argument
    voidedStatementId: Optional[str] = Query(
        None, description="**Not implemented** Id of voided Statement to fetch"
    ),
    agent: Optional[Json] = Query(
        None,
        description=(
            "Filter, only return Statements for which the specified "
            "Agent or Group is the Actor or Object of the Statement"
        ),
    ),
    verb: Optional[str] = Query(
        None,
        description="Filter, only return Statements matching the specified Verb id",
    ),
    activity: Optional[str] = Query(
        None,
        description=(
            "Filter, only return Statements for which the Object "
            "of the Statement is an Activity with the specified id"
        ),
    ),
    # pylint: disable=unused-argument
    registration: Optional[UUID] = Query(
        None,
        description=(
            "**Not implemented** "
            "Filter, only return Statements matching the specified registration id"
        ),
    ),
    # pylint: disable=unused-argument
    related_activities: Optional[bool] = Query(
        False,
        description=(
            "**Not implemented** "
            "Apply the Activity filter broadly. Include Statements for which "
            "the Object, any of the context Activities, or any of those properties "
            "in a contained SubStatement match the Activity parameter, "
            "instead of that parameter's normal behaviour"
        ),
    ),
    # pylint: disable=unused-argument
    related_agents: Optional[bool] = Query(
        False,
        description=(
            "**Not implemented** "
            "Apply the Agent filter broadly. Include Statements for which "
            "the Actor, Object, Authority, Instructor, Team, or any of these "
            "properties in a contained SubStatement match the Agent parameter, "
            "instead of that parameter's normal behaviour."
        ),
    ),
    since: Optional[datetime] = Query(
        None,
        description=(
            "Only Statements stored since the "
            "specified Timestamp (exclusive) are returned"
        ),
    ),
    until: Optional[datetime] = Query(
        None,
        description=(
            "Only Statements stored at or "
            "before the specified Timestamp are returned"
        ),
    ),
    limit: Optional[int] = Query(
        settings.RUNSERVER_MAX_SEARCH_HITS_COUNT,
        description=(
            "Maximum number of Statements to return. "
            "0 indicates return the maximum the server will allow"
        ),
    ),
    # pylint: disable=unused-argument, redefined-builtin
    format: Optional[Literal["ids", "exact", "canonical"]] = Query(
        "exact",
        description=(
            "**Not implemented** "
            'If "ids", only include minimum information necessary in Agent, Activity, '
            "Verb and Group Objects to identify them. For Anonymous Groups this means "
            "including the minimum information needed to identify each member. "
            'If "exact", return Agent, Activity, Verb and Group Objects populated '
            "exactly as they were when the Statement was received. An LRS requesting "
            "Statements for the purpose of importing them would use a format of "
            '"exact" in order to maintain Statement Immutability. '
            'If "canonical", return Activity Objects and Verbs populated with the '
            "canonical definition of the Activity Objects and Display of the Verbs "
            "as determined by the LRS, after applying the language filtering process "
            "defined below, and return the original Agent and Group Objects "
            'as in "exact" mode.'
        ),
    ),
    # pylint: disable=unused-argument
    attachments: Optional[bool] = Query(
        False,
        description=(
            "**Not implemented** "
            'If "true", the LRS uses the multipart response format and includes '
            'all attachments as described previously. If "false", the LRS sends '
            "the prescribed response with Content-Type application/json and "
            "does not send attachment data."
        ),
    ),
    ascending: Optional[bool] = Query(
        False, description='If "true", return results in ascending order of stored time'
    ),
    ###
    # Private use query string parameters
    ###
    search_after: Optional[str] = Query(
        None,
        description=(
            "Sorting data to allow pagination through large number of search results. "
            "NB: for internal use, not part of the LRS specification."
        ),
    ),
    pit_id: Optional[str] = Query(
        None,
        description=(
            "Point-in-time ID to ensure consistency of search requests through "
            "multiple pages."
            "NB: for internal use, not part of the LRS specification."
        ),
    ),
):
    """Fetches a single xAPI Statement or multiple xAPI Statements.

    LRS Specification:
    https://github.com/adlnet/xAPI-Spec/blob/1.0.3/xAPI-Communication.md#213-get-statements
    """
    # Make sure the limit does not go above max from settings
    limit = min(limit, settings.RUNSERVER_MAX_SEARCH_HITS_COUNT)

    # 400 Bad Request for requests using both `statementId` and `voidedStatementId`
    if (statementId is not None) and (voidedStatementId is not None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Query parameters cannot include both `statementId`"
                "and `voidedStatementId`"
            ),
        )

    # 400 Bad Request for any request containing `statementId` or
    # `voidedStatementId` and any other parameter besides `attachments` or `format`.
    # NB: `limit` and `ascending` are not handled to simplify implementation, and as it
    # has no incidence on UX, when fetching a single statement
    excluded_params = [
        agent,
        verb,
        activity,
        registration,
        related_activities,
        related_agents,
        since,
        until,
    ]
    # NB: bool(param) relies on all defaults being None, 0, or False
    if (statementId or voidedStatementId) and any(
        bool(param) for param in excluded_params
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Querying by id only accepts `attachments` and `format` as extra"
                "parameters"
            ),
        )

    # Parse the agent parameter (JSON) into multiple string parameters
    query_params = dict(request.query_params)

    if query_params.get("agent") is not None:
        # Transform agent to `dict` as FastAPI cannot parse JSON (seen as string)

        agent = parse_raw_as(BaseXapiAgent, query_params["agent"])

        agent_query_params = {}
        if isinstance(agent, BaseXapiAgentWithMbox):
            agent_query_params["mbox"] = agent.mbox
        elif isinstance(agent, BaseXapiAgentWithMboxSha1Sum):
            agent_query_params["mbox_sha1sum"] = agent.mbox_sha1sum
        elif isinstance(agent, BaseXapiAgentWithOpenId):
            agent_query_params["openid"] = agent.openid
        elif isinstance(agent, BaseXapiAgentWithAccount):
            agent_query_params["account__name"] = agent.account.name
            agent_query_params["account__home_page"] = agent.account.homePage

        query_params["agent"] = AgentParameters(**agent_query_params)

    # Query Database
    try:
        query_result = DATABASE_CLIENT.query_statements(
            StatementParameters(**{**query_params, "limit": limit})
        )
    except BackendException as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="xAPI statements query failed",
        ) from error

    # Prepare the link to get the next page of the request, while preserving the
    # consistency of search results.
    # NB: There is an unhandled edge case where the total number of results is
    # exactly a multiple of the "limit", in which case we'll offer an extra page
    # with 0 results.
    response = {}
    if len(query_result.statements) == limit:
        # Search after relies on sorting info located in the last hit
        path = request.url.path
        query = dict(request.query_params)

        query.update(
            {
                "pit_id": query_result.pit_id,
                "search_after": query_result.search_after,
            }
        )

        response.update(
            {
                "more": ParseResult(
                    scheme="",
                    netloc="",
                    path=path,
                    params="",
                    query=urlencode(query),
                    fragment="",
                ).geturl(),
            }
        )

    return {**response, "statements": query_result.statements}


@router.put("/", responses=POST_PUT_RESPONSES, status_code=status.HTTP_204_NO_CONTENT)
@router.put("", responses=POST_PUT_RESPONSES, status_code=status.HTTP_204_NO_CONTENT)
# pylint: disable=unused-argument
async def put(
    # pylint: disable=invalid-name
    statementId: str,
    statement: LaxStatement,
    background_tasks: BackgroundTasks,
):
    """Stores a single statement as a single member of a set.

    LRS Specification:
    https://github.com/adlnet/xAPI-Spec/blob/1.0.3/xAPI-Communication.md#211-put-statements
    """
    statement_dict = {statementId: statement.dict(exclude_unset=True)}

    # Force the UUID id in the statement to string, make sure it matches the
    # statementId given in the URL.
    statement_dict[statementId]["id"] = str(statement_dict[statementId]["id"])

    if not statementId == statement_dict[statementId]["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="xAPI statement id does not match given statementId",
        )

    if get_active_xapi_forwardings():
        background_tasks.add_task(
            forward_xapi_statements, list(statement_dict.values())
        )

    try:
        statements_ids_result = DATABASE_CLIENT.query_statements_by_ids([statementId])
    except BackendException as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="xAPI statements query failed",
        ) from error

    if len(statements_ids_result) > 0:
        # NB: LRS specification calls for performing a deep comparison of incoming
        # statements and existing statements with the same ID.
        # This seems too costly for performance and was not implemented for this POC.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Statement already exists with the same ID",
        )

    # For valid requests, perform the bulk indexing of all incoming statements
    try:
        success_count = DATABASE_CLIENT.put(
            statement_dict.values(), ignore_errors=False
        )
    except (BackendException, BadFormatException) as exc:
        logger.error("Failed to index submitted statement")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Statement indexation failed",
        ) from exc

    logger.info("Indexed %d statements with success", success_count)


@router.post("/", responses=POST_PUT_RESPONSES)
@router.post("", responses=POST_PUT_RESPONSES)
async def post(
    statements: Union[LaxStatement, List[LaxStatement]],
    background_tasks: BackgroundTasks,
):
    """Stores a set of statements (or a single statement as a single member of a set).

    NB: at this time, using POST to make a GET request, is not supported.
    LRS Specification:
    https://github.com/adlnet/xAPI-Spec/blob/1.0.3/xAPI-Communication.md#212-post-statements
    """
    # As we accept both a single statement as a dict, and multiple statements as a list,
    # we need to normalize the data into a list in all cases before we can process it.
    if not isinstance(statements, list):
        statements = [statements]

    # The statements dict has multiple functions:
    # - generate IDs for statements that are missing them;
    # - use the list of keys to perform validations and as a final return value;
    # - provide an iterable containing both the statements and generated IDs for bulk.
    statements_dict = {}
    for statement in map(lambda x: x.dict(exclude_unset=True), statements):
        statement_id = str(statement.get("id", uuid4()))
        statement["id"] = statement_id
        statements_dict[statement_id] = statement

    # Requests with duplicate statement IDs are considered invalid
    # statements_ids were deduplicated by the dict, statements list was not
    statements_ids = list(statements_dict.keys())
    if len(statements) != len(statements_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate statement IDs in the list of statements",
        )

    if get_active_xapi_forwardings():
        background_tasks.add_task(
            forward_xapi_statements, list(statements_dict.values())
        )

    try:
        statements_ids_result = DATABASE_CLIENT.query_statements_by_ids(statements_ids)
    except BackendException as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="xAPI statements query failed",
        ) from error

    if len(statements_ids_result) > 0:
        # NB: LRS specification calls for performing a deep comparison of incoming
        # statements and existing statements with the same ID.
        # This seems too costly for performance and was not implemented for this POC.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Statements already exist with the same ID",
        )

    # For valid requests, perform the bulk indexing of all incoming statements
    try:
        success_count = DATABASE_CLIENT.put(
            statements_dict.values(), ignore_errors=False
        )
    except (BackendException, BadFormatException) as exc:
        logger.error("Failed to index submitted statements")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Statements bulk indexation failed",
        ) from exc

    logger.info("Indexed %d statements with success", success_count)

    return statements_ids
