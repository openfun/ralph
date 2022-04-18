"""API routes related to statements."""

import logging
from datetime import datetime
from typing import Literal, Optional, Union
from uuid import UUID, uuid4

from elasticsearch.helpers import BulkIndexError
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ralph.backends.database.es import ESDatabase

from ...defaults import ES_MAX_SEARCH_HITS_COUNT
from ..auth import authenticated_user
from ..models import ErrorDetail, LaxStatement

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/xAPI/statements",
    dependencies=[Depends(authenticated_user)],
)


ES_CLIENT = ESDatabase()


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
    # NB: ActorField, which is the specific type expected, is not valid as a query param
    agent: Optional[str] = Query(
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
        ES_MAX_SEARCH_HITS_COUNT,
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
    """
    Fetch a single xAPI Statement or multiple xAPI Statements.

    LRS Specification:
    https://github.com/adlnet/xAPI-Spec/blob/1.0.3/xAPI-Communication.md#213-get-statements
    """

    # Create a list to aggregate all the enabled filters for the search
    es_query_filters = []

    if statementId:
        es_query_filters += [{"term": {"_id": statementId}}]

    if agent:
        es_query_filters += [{"term": {"actor.account.name.keyword": agent}}]

    if verb:
        es_query_filters += [{"term": {"verb.id.keyword": verb}}]

    if activity:
        es_query_filters += [
            {"term": {"object.objectType.keyword": "Activity"}},
            {"term": {"object.id.keyword": activity}},
        ]

    if since:
        es_query_filters += [{"range": {"timestamp": {"gt": since}}}]

    if until:
        es_query_filters += [{"range": {"timestamp": {"lte": until}}}]

    if len(es_query_filters) > 0:
        es_query = {"query": {"bool": {"filter": es_query_filters}}}
    else:
        es_query = {"query": {"match_all": {}}}

    # Honor the "ascending" parameter, otherwise show most recent statements first
    es_query.update(
        {"sort": [{"timestamp": {"order": "asc" if ascending else "desc"}}]}
    )

    if search_after:
        es_query.update({"search_after": search_after.split("|")})

    # Disable total hits counting for performance as we're not using it.
    es_query.update({"track_total_hits": False})

    # Make sure the limit does not go above max from settings
    limit = min(limit, ES_MAX_SEARCH_HITS_COUNT)

    es_response = ES_CLIENT.query(es_query, limit, pit_id)

    # Prepare the link to get the next page of the request, while preserving the
    # consistency of search results.
    # NB: There is an unhandled edge case where the total number of results is
    # exactly a multiple of the "limit", in which case we'll offer an extra page
    # with 0 results.
    response = {}
    if len(es_response["hits"]["hits"]) == limit:
        # Search after relies on sorting info located in the last hit
        last_hit_sort = [str(part) for part in es_response["hits"]["hits"][-1]["sort"]]
        pit_id = es_response["pit_id"]
        path = request.url.components.path
        query = request.url.components.query
        response.update(
            {
                "more": (
                    f"{path}{query + '&' if query else '?'}pit_id={pit_id}"
                    f"&search_after={'|'.join(last_hit_sort)}"
                )
            }
        )

    return {
        **response,
        "statements": [
            statement["_source"] for statement in es_response["hits"]["hits"]
        ],
    }


@router.post(
    "/",
    responses={
        400: {
            "model": ErrorDetail,
            "description": "The request was invalid.",
        },
        409: {
            "model": ErrorDetail,
            "description": "Statements had a conflict with existing statements.",
        },
    },
)
# pylint: disable=unused-argument
async def post(statements: Union[LaxStatement, list[LaxStatement]]):
    """
    Store a set of statements (or a single statement as a single member of a set).
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
    statements_dict = {
        statement.setdefault("id", str(uuid4())): statement
        for statement in map(lambda x: x.dict(exclude_unset=True), statements)
    }

    # Requests with duplicate statement IDs are considered invalid
    # statements_ids were deduplicated by the dict, statements list was not
    statements_ids = list(statements_dict.keys())
    if len(statements) != len(statements_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate statement IDs in the list of statements",
        )

    es_response = ES_CLIENT.query({"query": {"terms": {"_id": statements_ids}}})

    if len(es_response["hits"]["hits"]) > 0:
        # NB: LRS specification calls for performing a deep comparison of incoming
        # statements and existing statements with the same ID.
        # This seems too costly for performance and was not implemented for this POC.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Statements already exist with the same ID",
        )

    # For valid requests, perform the bulk indexing of all incoming statements
    try:
        ES_CLIENT.put(statements_dict.values(), ignore_errors=False)
    except BulkIndexError as exc:
        logger.error("Failed to index submitted statements")
        raise HTTPException(
            status_code=500, detail="Statements bulk indexation failed"
        ) from exc

    logger.info("Indexed %d statements with success", len(statements_dict))

    return statements_ids
