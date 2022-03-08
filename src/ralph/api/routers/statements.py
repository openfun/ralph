"""API routes related to statements."""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch
from fastapi import APIRouter, Depends, Query, Request

from ...defaults import ES_HOSTS, ES_MAX_SEARCH_HITS_COUNT, ES_POINT_IN_TIME_KEEP_ALIVE
from ..auth import authenticated_user

router = APIRouter(
    prefix="/xAPI/statements",
    dependencies=[Depends(authenticated_user)],
)


ES_CLIENT = AsyncElasticsearch(ES_HOSTS)


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
            "instead of that parameter's normal behavior"
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
            "instead of that parameter's normal behavior."
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

    # Create a point-in-time or use the existing one to ensure consistency of search
    # results over multiple pages.
    if not pit_id:
        # pylint: disable=unexpected-keyword-arg
        pit_response = await ES_CLIENT.open_point_in_time(
            index="statements", keep_alive=ES_POINT_IN_TIME_KEEP_ALIVE
        )
        pit_id = pit_response["id"]
    es_query.update(
        {
            "pit": {
                "id": pit_id,
                # extend duration of PIT whenever it is used
                "keep_alive": ES_POINT_IN_TIME_KEEP_ALIVE,
            }
        }
    )

    if search_after:
        es_query.update({"search_after": search_after.split("|")})

    # Disable total hits counting for performance as we're not using it.
    es_query.update({"track_total_hits": False})

    # Make sure the limit does not go above max from settings
    limit = min(limit, ES_MAX_SEARCH_HITS_COUNT)

    # pylint: disable=unexpected-keyword-arg
    es_response = await ES_CLIENT.search(
        body=es_query,
        size=limit,
    )

    # Prepare the link to get the next page of the request, while preserving the
    # consistency of search results.
    # NB: There is an unhandled edge case where the total number of results is
    # exactly a multiple of the "limit", in which case we'll offer an extra page
    # with 0 results.
    response = {}
    if len(es_response["hits"]["hits"]) == limit:
        # Search after relies on sorting info located in the last hit
        last_hit_sort = [str(part) for part in es_response["hits"]["hits"][-1]["sort"]]
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
