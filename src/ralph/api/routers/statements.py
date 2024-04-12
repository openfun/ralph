"""API routes related to statements."""

import json
import logging
from datetime import datetime
from typing import Dict, List, Literal, Optional, Union
from urllib.parse import ParseResult, urlencode
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    Security,
    status,
)
from fastapi.dependencies.models import Dependant
from pydantic import TypeAdapter
from pydantic.types import Json
from typing_extensions import Annotated

from ralph.api.auth import get_authenticated_user
from ralph.api.auth.user import AuthenticatedUser
from ralph.api.forwarding import forward_xapi_statements, get_active_xapi_forwardings
from ralph.api.models import ErrorDetail, LaxStatement
from ralph.backends.loader import get_lrs_backends
from ralph.backends.lrs.base import (
    AgentParameters,
    BaseAsyncLRSBackend,
    BaseLRSBackend,
    RalphStatementsQuery,
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
from ralph.models.xapi.base.common import IRI
from ralph.utils import (
    await_if_coroutine,
    get_backend_class,
    now,
    statements_are_equivalent,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/xAPI/statements",
    dependencies=[Depends(get_authenticated_user)],
)


BACKEND_CLIENT: Union[BaseLRSBackend, BaseAsyncLRSBackend] = get_backend_class(
    backends=get_lrs_backends(), name=settings.RUNSERVER_BACKEND
)()

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


def _enrich_statement_with_id(statement: dict) -> None:
    # id: Statement UUID identifier.
    # https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#24-statement-properties
    statement["id"] = str(statement.get("id", uuid4()))


def _enrich_statement_with_stored(statement: dict) -> None:
    # stored: The time at which a Statement is stored by the LRS.
    # https://github.com/adlnet/xAPI-Spec/blob/1.0.3/xAPI-Data.md#248-stored
    statement["stored"] = now()


def _enrich_statement_with_timestamp(statement: dict) -> None:
    # timestamp: Time of the action. If not provided, it takes the same value as stored.
    # https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#247-timestamp
    statement["timestamp"] = statement.get("timestamp", statement["stored"])


def _enrich_statement_with_authority(
    statement: dict, current_user: AuthenticatedUser
) -> None:
    # authority: Information about whom or what has asserted the statement is true.
    # https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#249-authority
    statement["authority"] = current_user.agent.model_dump(
        exclude_none=True, mode="json"
    )


def _parse_agent_parameters(agent_obj: dict) -> AgentParameters:
    """Parse a dict and return an AgentParameters object to use in queries."""
    # Transform agent to `dict` as FastAPI cannot parse JSON (seen as string)

    adapter = TypeAdapter(BaseXapiAgent)
    agent = adapter.validate_python(agent_obj)

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

    # Overwrite `agent` field
    return AgentParameters.model_construct(**agent_query_params)


def strict_query_params(request: Request) -> None:
    """Raise a 400 error when using extra query parameters."""
    dependant: Dependant = request.scope["route"].dependant
    allowed_params = [
        param.alias
        for dependency in dependant.dependencies
        for param in dependency.query_params
    ]
    allowed_params += [modelfield.alias for modelfield in dependant.query_params]
    for requested_param in request.query_params.keys():
        if requested_param not in allowed_params:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The following parameter is not allowed: `{requested_param}`",
            )


@router.get("")
@router.get("/")
async def get(  # noqa: PLR0912,PLR0913
    request: Request,
    current_user: Annotated[
        AuthenticatedUser,
        Security(get_authenticated_user, scopes=["statements/read/mine"]),
    ],
    ###
    # Query string parameters defined by the LRS specification
    ###
    statement_id: Annotated[
        Optional[str],
        Query(description="Id of Statement to fetch", alias="statementId"),
    ] = None,
    voided_statement_id: Annotated[
        Optional[str],
        Query(
            description="**Not implemented** Id of voided Statement to fetch",
            alias="voidedStatementId",
        ),
    ] = None,
    agent: Annotated[
        Optional[Json],
        Query(
            description=(
                "Filter, only return Statements for which the specified "
                "Agent or Group is the Actor or Object of the Statement"
            ),
        ),
    ] = None,
    verb: Annotated[
        Optional[str],
        Query(
            description="Filter, only return Statements matching the specified Verb id",
        ),
    ] = None,
    activity: Annotated[
        Optional[str],
        Query(
            description=(
                "Filter, only return Statements for which the Object "
                "of the Statement is an Activity with the specified id"
            ),
        ),
    ] = None,
    registration: Annotated[
        Optional[UUID],
        Query(
            description=(
                "**Not implemented** "
                "Filter, only return Statements matching the specified registration id"
            ),
        ),
    ] = None,
    related_activities: Annotated[
        Optional[bool],
        Query(
            description=(
                "**Not implemented** "
                "Apply the Activity filter broadly. Include Statements for which "
                "the Object, any of the context Activities, or any of those properties "
                "in a contained SubStatement match the Activity parameter, "
                "instead of that parameter's normal behaviour"
            ),
        ),
    ] = False,
    related_agents: Annotated[
        Optional[bool],
        Query(
            description=(
                "**Not implemented** "
                "Apply the Agent filter broadly. Include Statements for which "
                "the Actor, Object, Authority, Instructor, Team, or any of these "
                "properties in a contained SubStatement match the Agent parameter, "
                "instead of that parameter's normal behaviour."
            ),
        ),
    ] = False,
    since: Annotated[
        Optional[datetime],
        Query(
            description=(
                "Only Statements stored since the "
                "specified Timestamp (exclusive) are returned"
            ),
        ),
    ] = None,
    until: Annotated[
        Optional[datetime],
        Query(
            description=(
                "Only Statements stored at or "
                "before the specified Timestamp are returned"
            ),
        ),
    ] = None,
    limit: Annotated[
        Optional[int],
        Query(
            ge=0,
            description=(
                "Maximum number of Statements to return. "
                "0 indicates return the maximum the server will allow"
            ),
        ),
    ] = settings.RUNSERVER_MAX_SEARCH_HITS_COUNT,
    format: Annotated[  # noqa: ARG001
        Optional[Literal["ids", "exact", "canonical"]],
        Query(
            description=(
                "**Not implemented** "
                'If "ids", only include minimum information necessary in Agent, '
                "Activity, Verb and Group Objects to identify them. For Anonymous "
                "Groups this means including the minimum information needed to "
                'identify each member. If "exact", return Agent, Activity, Verb and '
                "Group Objects populated exactly as they were when the Statement was "
                "received. An LRS requesting Statements for the purpose of importing "
                'them would use a format of "exact" in order to maintain Statement '
                'Immutability. If "canonical", return Activity Objects and Verbs '
                "populated with the canonical definition of the Activity Objects and "
                "Display of the Verbs  as determined by the LRS, after applying the "
                "language filtering process  defined below, and return the original "
                'Agent and Group Objects as in "exact" mode.'
            ),
        ),
    ] = "exact",
    attachments: Annotated[  # noqa: ARG001
        Optional[bool],
        Query(
            description=(
                "**Not implemented** "
                'If "true", the LRS uses the multipart response format and includes '
                'all attachments as described previously. If "false", the LRS sends '
                "the prescribed response with Content-Type application/json and "
                "does not send attachment data."
            ),
        ),
    ] = False,
    ascending: Annotated[  # noqa: ARG001
        Optional[bool],
        Query(
            description='If "true", return results in ascending order of stored time'
        ),
    ] = False,
    mine: Annotated[
        Optional[bool],
        Query(
            description=(
                'If "true", return only the results for which the authority matches '
                'the "agent" associated to the user that is making the query.'
            ),
        ),
    ] = False,
    ###
    # Private use query string parameters
    ###
    search_after: Annotated[  # noqa: ARG001
        Optional[str],
        Query(
            description=(
                "Sorting data to allow pagination through large number of search "
                "results."
                "NB: for internal use, not part of the LRS specification."
            ),
        ),
    ] = None,
    pit_id: Annotated[  # noqa: ARG001
        Optional[str],
        Query(
            description=(
                "Point-in-time ID to ensure consistency of search requests through "
                "multiple pages."
                "NB: for internal use, not part of the LRS specification."
            ),
        ),
    ] = None,
    _=Depends(strict_query_params),
) -> Dict:
    """Read a single xAPI Statement or multiple xAPI Statements.

    LRS Specification:
    https://github.com/adlnet/xAPI-Spec/blob/1.0.3/xAPI-Communication.md#213-get-statements
    """
    # Make sure the limit does not go above max from settings
    limit = min(limit, settings.RUNSERVER_MAX_SEARCH_HITS_COUNT)

    # 400 Bad Request for requests using both `statement_id` and `voided_statement_id`
    if (statement_id is not None) and (voided_statement_id is not None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Query parameters cannot include both `statementId`"
                "and `voidedStatementId`"
            ),
        )

    # 400 Bad Request for any request containing `statement_id` or
    # `voided_statement_id` and any other parameter besides `attachments` or `format`.
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
    if (statement_id or voided_statement_id) and any(
        bool(param) for param in excluded_params
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Querying by id only accepts `attachments` and `format` as extra "
                "parameters"
            ),
        )

    query_params = dict(request.query_params)

    # Parse the "agent" parameter (JSON) into multiple string parameters
    if query_params.get("agent") is not None:
        # Overwrite `agent` field
        query_params["agent"] = _parse_agent_parameters(
            json.loads(query_params["agent"])
        ).model_dump(mode="json", exclude_none=True)

    # Coerce `verb` and `activity` as IRI
    if query_params.get("verb"):
        query_params["verb"] = IRI(query_params["verb"])

    if query_params.get("activity"):
        query_params["activity"] = IRI(query_params["activity"])

    # mine: If using scopes, only restrict users with limited scopes
    if settings.LRS_RESTRICT_BY_SCOPES:
        if not current_user.scopes.is_authorized("statements/read"):
            mine = True
    # mine: If using only authority, always restrict (otherwise, use the default value)
    elif settings.LRS_RESTRICT_BY_AUTHORITY:
        mine = True

    # Filter by authority if using `mine`
    if mine:
        query_params["authority"] = _parse_agent_parameters(
            current_user.agent.model_dump(mode="json")
        ).model_dump(mode="json", exclude_none=True)

    if "mine" in query_params:
        query_params.pop("mine")

    # Query Database
    try:
        query_result = await await_if_coroutine(
            BACKEND_CLIENT.query_statements(
                params=RalphStatementsQuery.model_construct(
                    **{**query_params, "limit": limit}
                ),
                target=current_user.target,
            )
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
async def put(
    current_user: Annotated[
        AuthenticatedUser,
        Security(get_authenticated_user, scopes=["statements/write"]),
    ],
    statement: LaxStatement,
    background_tasks: BackgroundTasks,
    statement_id: UUID = Query(alias="statementId"),
    _=Depends(strict_query_params),
) -> None:
    """Store a single statement as a single member of a set.

    LRS Specification:
    https://github.com/adlnet/xAPI-Spec/blob/1.0.3/xAPI-Communication.md#211-put-statements
    """
    statement_as_dict = statement.model_dump(exclude_unset=True, mode="json")
    statement_id = str(statement_id)

    statement_as_dict.update(id=str(statement_as_dict.get("id", statement_id)))
    if statement_id != statement_as_dict["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="xAPI statement id does not match given statementId",
        )

    # Enrich statement before forwarding (NB: id is already set)
    _enrich_statement_with_stored(statement_as_dict)
    _enrich_statement_with_timestamp(statement_as_dict)

    if get_active_xapi_forwardings():
        background_tasks.add_task(
            forward_xapi_statements, statement_as_dict, method="put"
        )

    # Finish enriching statements after forwarding
    _enrich_statement_with_authority(statement_as_dict, current_user)

    try:
        if isinstance(BACKEND_CLIENT, BaseLRSBackend):
            existing_statements = list(
                BACKEND_CLIENT.query_statements_by_ids(
                    ids=[statement_id], target=current_user.target
                )
            )
        else:
            existing_statements = [
                x
                async for x in BACKEND_CLIENT.query_statements_by_ids(
                    ids=[statement_id], target=current_user.target
                )
            ]
    except BackendException as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="xAPI statements query failed",
        ) from error

    if existing_statements:
        # The LRS specification calls for deep comparison of duplicate statement ids.
        # In the case that the current statement is not equivalent to one found
        # in the database we return a 409, otherwise the usual 204.
        for existing in existing_statements:
            if not statements_are_equivalent(statement_as_dict, existing):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A different statement already exists with the same ID",
                )
        return

    # For valid requests, perform the bulk indexing of all incoming statements
    try:
        success_count = await await_if_coroutine(
            BACKEND_CLIENT.write(
                data=[statement_as_dict],
                target=current_user.target,
                ignore_errors=False,
            )
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
async def post(  # noqa: PLR0912
    current_user: Annotated[
        AuthenticatedUser,
        Security(get_authenticated_user, scopes=["statements/write"]),
    ],
    statements: Union[LaxStatement, List[LaxStatement]],
    background_tasks: BackgroundTasks,
    response: Response,
    _=Depends(strict_query_params),
) -> Union[List, None]:
    """Store a set of statements (or a single statement as a single member of a set).

    NB: at this time, using POST to make a GET request, is not supported.
    LRS Specification:
    https://github.com/adlnet/xAPI-Spec/blob/1.0.3/xAPI-Communication.md#212-post-statements
    """
    # As we accept both a single statement as a dict, and multiple statements as a list,
    # we need to normalize the data into a list in all cases before we can process it.
    if not isinstance(statements, list):
        statements = [statements]

    # Enrich statements before forwarding
    statements_dict = {}
    for statement in (
        x.model_dump(exclude_unset=True, mode="json") for x in statements
    ):
        _enrich_statement_with_id(statement)
        # Requests with duplicate statement IDs are considered invalid
        if statement["id"] in statements_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate statement IDs in the list of statements",
            )
        _enrich_statement_with_stored(statement)
        _enrich_statement_with_timestamp(statement)
        _enrich_statement_with_authority(statement, current_user)
        statements_dict[statement["id"]] = statement

    # Forward statements
    if get_active_xapi_forwardings():
        background_tasks.add_task(
            forward_xapi_statements, list(statements_dict.values()), method="post"
        )

    try:
        if isinstance(BACKEND_CLIENT, BaseLRSBackend):
            existing_statements = list(
                BACKEND_CLIENT.query_statements_by_ids(
                    ids=list(statements_dict), target=current_user.target
                )
            )
        else:
            existing_statements = [
                x
                async for x in BACKEND_CLIENT.query_statements_by_ids(
                    ids=list(statements_dict), target=current_user.target
                )
            ]
    except BackendException as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="xAPI statements query failed",
        ) from error

    # If there are duplicate statements, remove them from our id list and
    # dictionary for insertion. We will return the shortened list of ids below
    # so that consumers can derive which statements were inserted and which
    # were skipped for being duplicates.
    # See: https://github.com/openfun/ralph/issues/345
    if existing_statements:
        existing_ids = set()
        for existing in existing_statements:
            existing_ids.add(existing["id"])

            # The LRS specification calls for deep comparison of duplicates. This
            # is done here. If they are not exactly the same, we raise an error.
            if not statements_are_equivalent(statements_dict[existing["id"]], existing):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Differing statements already exist with the same ID: "
                    f"{existing['id']}",
                )

        # Filter existing statements from the incoming statements
        statements_dict = {
            key: value
            for key, value in statements_dict.items()
            if key not in existing_ids
        }
        if not statements_dict:
            response.status_code = status.HTTP_204_NO_CONTENT
            return

    # For valid requests, perform the bulk indexing of all incoming statements
    try:
        success_count = await await_if_coroutine(
            BACKEND_CLIENT.write(
                data=statements_dict.values(),
                target=current_user.target,
                ignore_errors=False,
            )
        )
    except (BackendException, BadFormatException) as exc:
        logger.error("Failed to index submitted statements")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Statements bulk indexation failed",
        ) from exc

    logger.info("Indexed %d statements with success", success_count)

    # Return the list of IDs in the same order they were stored
    return list(statements_dict)
