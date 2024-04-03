"""Utilities for testing Ralph."""

import hashlib
import random
import time
import uuid
from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from ralph.api.auth import AuthBackend
from ralph.utils import statements_are_equivalent

from tests.fixtures.auth import AUDIENCE, ISSUER_URI


def string_is_date(string: str):
    """Check if string can be parsed as a date."""
    try:
        datetime.fromisoformat(string)
        return True
    except ValueError:
        return False


def string_is_uuid(string: str):
    """Check if string is a valid uuid."""
    try:
        uuid.UUID(string)
        return True
    except ValueError:
        return False


def assert_statement_get_responses_are_equivalent(response_1: dict, response_2: dict):
    """Check that responses to GET /statements are equivalent.

    Check that all statements in response are equivalent, meaning that all
    fields not modified by the LRS are equal.
    """

    assert response_1.keys() == response_2.keys()

    def _all_but_statements(response):
        return {key: val for key, val in response.items() if key != "statements"}

    assert _all_but_statements(response_1) == _all_but_statements(response_2)

    # Assert the statements part of the response is equivalent
    assert "statements" in response_1.keys()
    assert "statements" in response_2.keys()
    assert len(response_1["statements"]) == len(response_2["statements"])

    for statement_1, statement_2 in zip(
        response_1["statements"], response_2["statements"]
    ):
        assert statements_are_equivalent(
            statement_1, statement_2
        ), "Statements in get responses are not equivalent, or not in the same order."


def mock_activity(id_: int = 0):
    """Create distinct activites with valid IRIs.

    Args:
        id_: An integer used to uniquely identify the created agent.

    """
    return {
        "id": f"http://example.com/activity_{id_}",
    }


def mock_agent(
    ifi: str = "mbox",
    id_: int = 1,
    home_page_id: Optional[int] = None,
    name: Optional[str] = None,
    use_object_type: bool = True,
):
    """Create distinct mock agents with a given Inverse Functional Identifier.

    Args:
        ifi: Inverse Functional Identifier. Possible values are:
            'mbox', 'mbox_sha1sum', 'openid' and 'account'.
        id_: An integer used to uniquely identify the created agent.
            If ifi=="account", agent equality requires same (id_, home_page_id).
        home_page_id: The value of homePage, if ifi=="account".
        name: Name of the agent (NB: do not confuse with account.name
            with ifi=="account", or "username", as used in credentials).
        use_object_type: Whether or not to create an `objectType` field with
            the value "Agent".
    """
    agent = {}

    if use_object_type:
        agent["objectType"] = "Agent"

    if name is not None:
        agent["name"] = name

    # Add IFI fields
    if ifi == "mbox":
        agent["mbox"] = f"mailto:user_{id_}@testmail.com"
        return agent

    if ifi == "mbox_sha1sum":
        hash_object = hashlib.sha1(f"mailto:user_{id_}@testmail.com".encode("utf-8"))
        mail_hash = hash_object.hexdigest()
        agent["mbox_sha1sum"] = mail_hash
        return agent

    if ifi == "openid":
        agent["openid"] = f"http://user_{id_}.openid.exmpl.org"
        return agent

    if ifi == "account":
        if home_page_id is None:
            raise ValueError(
                "home_page_id must be defined if using mock_agent if "
                "using ifi=='account'"
            )
        agent["account"] = {
            "homePage": f"http://example_{home_page_id}.com",
            "name": f"username_{id_}",
        }
        return agent

    raise ValueError("No valid ifi was provided to mock_agent")


def mock_statement(
    id_: Optional[Union[UUID, int]] = None,
    actor: Optional[Union[dict, int]] = None,
    verb: Optional[Union[dict, int]] = None,
    object: Optional[Union[dict, int]] = None,
    timestamp: Optional[Union[str, int]] = None,
):
    """Generate fake statements with random or provided parameters.

    Fields `actor`, `verb`, `object`, `timestamp` accept integer values which
    can be used to create distinct values identifiable by this integer. For each
    variable, using `None` will assign a default value. `timestamp` may be ommited
    by using value `""`
    Args:
        id_: id of the statement
        actor: actor of the statement
        verb: verb of the statement
        object: object of the statement
        timestamp: timestamp of the statement. Use `""` to omit timestamp
    """

    # Id
    if id_ is None:
        id_ = str(uuid.uuid4())

    # Actor
    if actor is None:
        actor = mock_agent()
    elif isinstance(actor, int):
        actor = mock_agent(id_=actor)

    # Verb
    if verb is None:
        verb = {"id": f"https://w3id.org/xapi/video/verbs/{random.random()}"}
    elif isinstance(verb, int):
        verb = {"id": f"https://w3id.org/xapi/video/verbs/{verb}"}

    # Object
    if object is None:
        object = {
            "id": f"http://example.adlnet.gov/xapi/example/activity_{random.random()}"
        }
    elif isinstance(object, int):
        object = {"id": f"http://example.adlnet.gov/xapi/example/activity_{object}"}

    # Timestamp
    if timestamp is None:
        timestamp = datetime.strftime(
            datetime.fromtimestamp(time.time() - random.random()),
            "%Y-%m-%dT%H:%M:%S+00:00",
        )
    elif isinstance(timestamp, int):
        timestamp = datetime.strftime(
            datetime.fromtimestamp(1696236665 + timestamp), "%Y-%m-%dT%H:%M:%S+00:00"
        )
    elif timestamp == "":
        return {
            "id": id_,
            "actor": actor,
            "verb": verb,
            "object": object,
        }

    return {
        "id": id_,
        "actor": actor,
        "verb": verb,
        "object": object,
        "timestamp": timestamp,
    }


def configure_env_for_mock_oidc_auth(
    monkeypatch, runserver_auth_backends: List[AuthBackend] = None
):
    """Configure environment variables to simulate OIDC use."""

    if runserver_auth_backends is None:
        runserver_auth_backends = [AuthBackend.OIDC]

    monkeypatch.setenv(
        "RUNSERVER_AUTH_BACKENDS",
        ",".join([backend.value for backend in runserver_auth_backends]),
    )
    monkeypatch.setattr(
        "ralph.api.auth.settings.RUNSERVER_AUTH_BACKENDS", runserver_auth_backends
    )
    monkeypatch.setattr(
        "ralph.api.auth.oidc.settings.RUNSERVER_AUTH_OIDC_ISSUER_URI",
        ISSUER_URI,
    )
    monkeypatch.setattr(
        "ralph.api.auth.oidc.settings.RUNSERVER_AUTH_OIDC_AUDIENCE",
        AUDIENCE,
    )
