from datetime import datetime
from typing import Literal, Optional, Union
from uuid import UUID

from elasticsearch import Elasticsearch  # NB: should be AsyncElasticsearch
from fastapi import APIRouter, Body, Depends, Query

from ...models.xapi.fields.actors import ActorField
from ..auth import authenticated_user


MAX_SEARCH_HITS = 100


router = APIRouter(
    prefix="/xAPI/statements",
    dependencies=[Depends(authenticated_user)],
)


es = Elasticsearch()


@router.get("/")
async def get(
    statementId: Optional[str] = Query(None, description="Id of Statement to fetch"),
    voidedStatementId: Optional[str] = Query(
        None, description="Id of voided Statement to fetch"
    ),
    # NB: ActorField, which is the specific type expected, is not valid as a query param
    agent: Optional[str] = Query(
        None,
        description=(
            "Filter, only return Statements for which the specified "
            "Agent or Group is the Actor or Object of the Statement"
        ),
    ),
    verb: Optional[str] = Query(  # NB: IRI
        None,
        description="Filter, only return Statements matching the specified Verb id",
    ),
    activity: Optional[str] = Query(  # NB: IRI
        None,
        description=(
            "Filter, only return Statements for which the Object "
            "of the Statement is an Activity with the specified id"
        ),
    ),
    registration: Optional[UUID] = Query(
        None,
        description="Filter, only return Statements matching the specified registration id",
    ),
    related_activities: Optional[bool] = Query(
        False,
        description=(
            "Apply the Activity filter broadly. Include Statements for which "
            "the Object, any of the context Activities, or any of those properties "
            "in a contained SubStatement match the Activity parameter, "
            "instead of that parameter's normal behavior"
        ),
    ),
    related_agents: Optional[bool] = Query(
        False,
        description=(
            "Apply the Agent filter broadly. Include Statements for which "
            "the Actor, Object, Authority, Instructor, Team, or any of these properties "
            "in a contained SubStatement match the Agent parameter, "
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
        0,
        description=(
            "Maximum number of Statements to return. "
            "0 indicates return the maximum the server will allow"
        ),
    ),
    format: Optional[Literal["ids", "exact", "canonical"]] = Query(
        "exact",
        description=(
            'If "ids", only include minimum information necessary in Agent, Activity, '
            "Verb and Group Objects to identify them. For Anonymous Groups this means "
            "including the minimum information needed to identify each member. "
            'If "exact", return Agent, Activity, Verb and Group Objects populated exactly '
            "as they were when the Statement was received. An LRS requesting Statements "
            'for the purpose of importing them would use a format of "exact" in order to '
            "maintain Statement Immutability. "
            'If "canonical", return Activity Objects and Verbs populated with the canonical '
            "definition of the Activity Objects and Display of the Verbs as determined by "
            "the LRS, after applying the language filtering process defined below, "
            'and return the original Agent and Group Objects as in "exact" mode.'
        ),
    ),
    attachments: Optional[bool] = Query(
        False,
        description=(
            'If "true", the LRS uses the multipart response format and includes '
            'all attachments as described previously. If "false", the LRS sends '
            "the prescribed response with Content-Type application/json and "
            "does not send attachment data."
        ),
    ),
    ascending: Optional[bool] = Query(
        False, description='If "true", return results in ascending order of stored time'
    ),
):
    """Fetch a single xAPI Statement or multiple xAPI Statements."""

    # Create a list to aggregate all the enabled filters for the search
    es_query_filters = []

    if statementId:
        es_query_filters += [{"term": {"id": statementId}}]

    if voidedStatementId:
        es_query_filters += [
            {"term": {"is_voided": True}},
            {"term": {"id": voidedStatementId}},
        ]

    if verb:
        es_query_filters += [{"term": {"verb": verb}}]

    if activity:
        if related_activities:
            es_query_filters += [{"term": {"related_activities": activity}}]
        else:
            es_query_filters += [{"term": {"activity": activity}}]

    if registration:
        es_query_filters += [{"term": {"registration": registration}}]

    if since:
        es_query_filters += [{"range": {"timestamp": {"gt": since}}}]

    if until:
        es_query_filters += [{"range": {"timestamp": {"lte": until}}}]

    if len(es_query_filters > 0):
        es_query = {"query": {"bool": {"filter": es_query_filters}}}
    else:
        es_query = {"match_all": {}}

    es_response = await es.search(
        index="statements",
        query=es_query,
        size=limit if limit else MAX_SEARCH_HITS,
    )

    return {"message": "Called xAPI GET statements"}
