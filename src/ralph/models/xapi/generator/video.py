"""xAPI video events model generator"""

import json
from datetime import datetime
from uuid import uuid4

import click
from hypothesis import HealthCheck, given, provisional, settings
from hypothesis import strategies as st

from ralph.models.xapi.fields.actors import ActorAccountField, ActorField
from ralph.models.xapi.video.fields.contexts import (
    VideoCompletedContextField,
    VideoInitializedContextField,
    VideoInteractedContextField,
    VideoPausedContextField,
    VideoPlayedContextField,
    VideoSeekedContextField,
    VideoTerminatedContextField,
)
from ralph.models.xapi.video.fields.objects import (
    VideoObjectDefinitionField,
    VideoObjectField,
)
from ralph.models.xapi.video.fields.results import (
    VideoCompletedResultField,
    VideoInteractedResultField,
    VideoPausedResultField,
    VideoPlayedResultField,
    VideoSeekedResultField,
    VideoTerminatedResultField,
)
from ralph.models.xapi.video.fields.verbs import (
    VideoCompletedVerbField,
    VideoInitializedVerbField,
    VideoInteractedVerbField,
    VideoPausedVerbField,
    VideoPlayedVerbField,
    VideoSeekedVerbField,
    VideoTerminatedVerbField,
)
from ralph.models.xapi.video.statements import (
    VideoCompleted,
    VideoInitialized,
    VideoInteracted,
    VideoPaused,
    VideoPlayed,
    VideoSeeked,
    VideoTerminated,
)


@settings(
    suppress_health_check=(HealthCheck.function_scoped_fixture,),
    max_examples=100,
)
@given(
    st.builds(
        VideoInitialized,
        id=st.builds(uuid4),
        timestamp=st.datetimes(
            min_value=datetime(2019, 1, 1), max_value=datetime(2021, 6, 30)
        ),
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoInitializedVerbField),
        context=st.builds(VideoInitializedContextField),
    )
)
def video_initalized_generate(statement):
    """Returns a random generated statement of VideoInitialized model."""

    statement = json.loads(statement.json())

    click.echo(statement)


@settings(
    max_examples=100, suppress_health_check=(HealthCheck.function_scoped_fixture,)
)
@given(
    st.builds(
        VideoPlayed,
        id=st.builds(uuid4),
        timestamp=st.datetimes(
            min_value=datetime(2019, 1, 1), max_value=datetime(2021, 6, 30)
        ),
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoPlayedVerbField),
        context=st.builds(VideoPlayedContextField),
        result=st.builds(VideoPlayedResultField),
    )
)
def video_played_generate(statement):
    """Returns a random generated statement of VideoPlayed model."""

    statement = json.loads(statement.json())

    click.echo(statement)


@settings(
    suppress_health_check=(HealthCheck.function_scoped_fixture,),
    max_examples=100,
)
@given(
    st.builds(
        VideoPaused,
        id=st.builds(uuid4),
        timestamp=st.datetimes(
            min_value=datetime(2019, 1, 1), max_value=datetime(2021, 6, 30)
        ),
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoPausedVerbField),
        context=st.builds(VideoPausedContextField),
        result=st.builds(VideoPausedResultField),
    )
)
def video_paused_generate(statement):
    """Returns a random generated statement of VideoPaused model."""

    statement = json.loads(statement.json())

    click.echo(statement)


@settings(
    suppress_health_check=(HealthCheck.function_scoped_fixture,),
    max_examples=100,
)
@given(
    st.builds(
        VideoSeeked,
        id=st.builds(uuid4),
        timestamp=st.datetimes(
            min_value=datetime(2019, 1, 1), max_value=datetime(2021, 6, 30)
        ),
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoSeekedVerbField),
        context=st.builds(VideoSeekedContextField),
        result=st.builds(VideoSeekedResultField),
    )
)
def video_seeked_generate(statement):
    """Returns a random generated statement of VideoSeeked model."""

    statement = json.loads(statement.json())

    click.echo(statement)


@settings(
    suppress_health_check=(HealthCheck.function_scoped_fixture,),
    max_examples=100,
)
@given(
    st.builds(
        VideoCompleted,
        id=st.builds(uuid4),
        timestamp=st.datetimes(
            min_value=datetime(2019, 1, 1), max_value=datetime(2021, 6, 30)
        ),
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoCompletedVerbField),
        context=st.builds(VideoCompletedContextField),
        result=st.builds(VideoCompletedResultField),
    )
)
def video_completed_generate(statement):
    """Returns a random generated statement of VideoCompleted model."""

    statement = json.loads(statement.json())

    click.echo(statement)


@settings(
    suppress_health_check=(HealthCheck.function_scoped_fixture,),
    max_examples=100,
)
@given(
    st.builds(
        VideoTerminated,
        id=st.builds(uuid4),
        timestamp=st.datetimes(
            min_value=datetime(2019, 1, 1), max_value=datetime(2021, 6, 30)
        ),
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoTerminatedVerbField),
        context=st.builds(VideoTerminatedContextField),
        result=st.builds(VideoTerminatedResultField),
    )
)
def video_terminated_generate(statement):
    """Returns a random generated statement of VideoTerminated model."""

    statement = json.loads(statement.json())

    click.echo(statement)


@settings(
    suppress_health_check=(HealthCheck.function_scoped_fixture,),
    max_examples=100,
)
@given(
    st.builds(
        VideoInteracted,
        id=st.builds(uuid4),
        timestamp=st.datetimes(
            min_value=datetime(2019, 1, 1), max_value=datetime(2021, 6, 30)
        ),
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoInteractedVerbField),
        context=st.builds(VideoInteractedContextField),
        result=st.builds(VideoInteractedResultField),
    )
)
def video_interacted_generate(statement):
    """Returns a random generated statement of VideoInteracted model."""

    statement = json.loads(statement.json())

    click.echo(statement)


# pylint: disable=no-value-for-parameter
def generate_video():
    """Generates groups of video events."""
    video_initalized_generate()
    video_played_generate()
    video_paused_generate()
    video_seeked_generate()
    video_completed_generate()
    video_terminated_generate()
    video_interacted_generate()
